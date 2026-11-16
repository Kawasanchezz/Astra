import os
import re
import zlib

import numpy as np
import pytest

from rag.chunking import Trecho, dividir_markdown
from rag.consulta import SEM_CONTEXTO, buscar_contexto, montar_mensagens, perguntar
from rag.embeddings import normalizar_linhas
from rag.indice import IndiceVetorial, indexar_pasta
from rag.prompts import ARQUIVOS, carregar_prompts, prompts_padrao

class EmbedderFalso:
    """Embedding por contagem de palavras (hash estável): barato, determinístico e com
    similaridade real, o suficiente para testar a busca sem baixar modelo."""
    nome = "falso-bow-256"

    def embed(self, textos):
        matriz = np.zeros((len(textos), 256), dtype=np.float32)
        for i, texto in enumerate(textos):
            for palavra in re.findall(r"\w+", texto.lower()):
                matriz[i, zlib.crc32(palavra.encode()) % 256] += 1.0
        return normalizar_linhas(matriz)

DOC_SQL = "# SQL\n\n## Joins\n\nO inner join devolve linhas com correspondência nas duas tabelas.\n"
DOC_GIT = "# Git\n\n## Branches\n\nUma branch isola o desenvolvimento de uma funcionalidade nova.\n"

@pytest.fixture
def pasta_docs(tmp_path):
    (tmp_path / "sql.md").write_text(DOC_SQL, encoding="utf-8")
    (tmp_path / "git.md").write_text(DOC_GIT, encoding="utf-8")
    return tmp_path

def test_divide_por_secao_e_guarda_o_caminho_do_titulo():
    md = "# Banco\n\n## ACID\n\nAtomicidade é tudo ou nada.\n\n## Índices\n\nAcelera consultas.\n"
    trechos = dividir_markdown(md, "banco.md")
    assert [(t.secao, t.texto) for t in trechos] == [
        ("Banco > ACID", "Atomicidade é tudo ou nada."),
        ("Banco > Índices", "Acelera consultas."),
    ]
    assert all(t.fonte == "banco.md" for t in trechos)

def test_nenhum_trecho_passa_do_limite_e_nada_se_perde():
    paragrafo = " ".join(f"palavra{i}" for i in range(200))
    trechos = dividir_markdown(f"# T\n\n{paragrafo}\n", "x.md", max_chars=200, sobreposicao=40)
    assert len(trechos) > 1
    assert all(len(t.texto) <= 200 for t in trechos)
    juntos = " ".join(t.texto for t in trechos)
    assert all(f"palavra{i}" in juntos for i in range(200))

def test_sobreposicao_repete_o_fim_do_trecho_anterior():
    paragrafo = " ".join(f"p{i}" for i in range(120))
    a, b = dividir_markdown(paragrafo, "x.md", max_chars=300, sobreposicao=60)[:2]
    assert a.texto.split()[-1] in b.texto.split()[:15]

def test_bloco_de_codigo_nao_e_dividido_nem_confundido_com_titulo():
    md = "# Python\n\nExemplo:\n\n```python\n# isto nao e titulo\nx = 1\n\ny = 2\n```\n"
    trechos = dividir_markdown(md, "py.md", max_chars=300)
    assert len(trechos) == 1
    assert "# isto nao e titulo" in trechos[0].texto and "y = 2" in trechos[0].texto
    assert trechos[0].secao == "Python"

def test_texto_vazio_nao_gera_trechos():
    assert dividir_markdown("\n\n  \n", "vazio.md") == []

def test_parametros_invalidos_sao_recusados():
    with pytest.raises(ValueError):
        dividir_markdown("texto", "x.md", max_chars=10)
    with pytest.raises(ValueError):
        dividir_markdown("texto", "x.md", max_chars=200, sobreposicao=150)

def test_secao_entra_no_texto_do_embedding():
    assert Trecho("a.md", "SQL > Joins", "texto").texto_para_embedding == "SQL > Joins\ntexto"
    assert Trecho("a.md", "", "texto").texto_para_embedding == "texto"

def test_busca_traz_o_trecho_certo_primeiro(pasta_docs):
    embedder = EmbedderFalso()
    indice = indexar_pasta(pasta_docs, embedder)
    achados = indice.buscar(embedder.embed(["como funciona o inner join entre tabelas"])[0], k=2)
    assert achados[0][0].fonte == "sql.md"
    assert achados[0][1] > achados[1][1]

def test_k_maior_que_o_indice_nao_quebra(pasta_docs):
    embedder = EmbedderFalso()
    indice = indexar_pasta(pasta_docs, embedder)
    assert len(indice.buscar(embedder.embed(["join"])[0], k=50)) == len(indice.trechos)

def test_salvar_e_carregar_devolve_os_mesmos_resultados(pasta_docs, tmp_path):
    embedder = EmbedderFalso()
    original = indexar_pasta(pasta_docs, embedder)
    saida = tmp_path / "indice"
    original.salvar(saida)
    carregado = IndiceVetorial.carregar(saida, modelo_esperado=embedder.nome)
    consulta = embedder.embed(["branch de funcionalidade"])[0]
    assert carregado.buscar(consulta, 2) == original.buscar(consulta, 2)

def test_carregar_com_outro_modelo_exige_reindexar(pasta_docs, tmp_path):
    saida = tmp_path / "indice"
    indexar_pasta(pasta_docs, EmbedderFalso()).salvar(saida)
    with pytest.raises(ValueError, match="reindexe"):
        IndiceVetorial.carregar(saida, modelo_esperado="outro-modelo")

def test_indexar_pasta_sem_documentos_falha_com_mensagem_clara(tmp_path):
    with pytest.raises(ValueError, match="nenhum trecho"):
        indexar_pasta(tmp_path, EmbedderFalso())

def test_score_minimo_descarta_trechos_sem_relacao(pasta_docs):
    embedder = EmbedderFalso()
    indice = indexar_pasta(pasta_docs, embedder)
    assert buscar_contexto(indice, embedder, "receita de bolo de cenoura", score_minimo=0.3) == []
    assert buscar_contexto(indice, embedder, "inner join", score_minimo=0.3)[0][0].fonte == "sql.md"

def test_prompt_leva_contexto_numerado_regra_e_pergunta():
    trecho = Trecho("sql.md", "SQL > Joins", "O inner join devolve linhas em comum.")
    mensagens = montar_mensagens("O que é inner join?", [(trecho, 0.9)])
    assert mensagens[0] == {"role": "system", "content": prompts_padrao().mensagem_sistema}
    usuario = mensagens[1]["content"]
    assert "[1] (fonte: sql.md > SQL > Joins)" in usuario
    assert "O inner join devolve linhas em comum." in usuario
    assert usuario.rstrip().endswith("Pergunta: O que é inner join?")

def test_pergunta_com_cifrao_e_chaves_nao_quebra_o_template():
    trecho = Trecho("a.md", "", "texto")
    pergunta = "Quanto é $contexto e ${pergunta} em {preco}?"
    assert pergunta in montar_mensagens(pergunta, [(trecho, 0.9)])[1]["content"]

def test_perguntar_chama_o_llm_com_o_contexto_e_devolve_as_fontes(pasta_docs):
    embedder = EmbedderFalso()
    indice = indexar_pasta(pasta_docs, embedder)
    recebido = []

    def llm_falso(mensagens):
        recebido.append(mensagens)
        return "Devolve só as linhas em comum [1]."

    resposta = perguntar("o que faz o inner join?", indice, embedder, llm_falso, score_minimo=0.3)
    assert resposta.usou_llm and resposta.texto == "Devolve só as linhas em comum [1]."
    assert resposta.fontes == ["sql.md"]
    assert "inner join" in recebido[0][1]["content"]

def test_sem_contexto_relevante_nao_chama_o_llm(pasta_docs):
    embedder = EmbedderFalso()
    indice = indexar_pasta(pasta_docs, embedder)

    def llm_proibido(_):
        raise AssertionError("o LLM não deveria ser chamado")

    resposta = perguntar("receita de bolo de cenoura", indice, embedder, llm_proibido, score_minimo=0.3)
    assert resposta.texto == SEM_CONTEXTO and not resposta.usou_llm and resposta.fontes == []

def _pasta_prompts(tmp_path, **alteracoes):
    textos = {"sistema.md": "sis", "regra-contexto.md": "regra", "formato.md": "fmt",
              "contexto.md": "C: $contexto | P: $pergunta"}
    textos.update(alteracoes)
    for nome, texto in textos.items():
        (tmp_path / nome).write_bytes(texto.encode("utf-8"))
    return tmp_path

def test_carrega_os_arquivos_e_compoe_a_mensagem_de_sistema(tmp_path):
    prompts = carregar_prompts(_pasta_prompts(tmp_path))
    assert prompts.mensagem_sistema == "sis\n\nregra\n\nfmt"
    assert prompts.mensagem_usuario("ctx", "perg") == "C: ctx | P: perg"

def test_versao_e_estavel_e_muda_com_o_conteudo(tmp_path):
    v1 = carregar_prompts(_pasta_prompts(tmp_path)).versao
    assert v1 == carregar_prompts(tmp_path).versao
    assert len(v1) == 10
    assert carregar_prompts(_pasta_prompts(tmp_path, **{"regra-contexto.md": "outra regra"})).versao != v1

def test_versao_ignora_quebra_de_linha_do_windows(tmp_path):
    lf = carregar_prompts(_pasta_prompts(tmp_path, **{"formato.md": "a\nb"})).versao
    crlf = carregar_prompts(_pasta_prompts(tmp_path, **{"formato.md": "a\r\nb"})).versao
    assert lf == crlf

def test_arquivo_ausente_ou_vazio_falha_com_mensagem_clara(tmp_path):
    pasta = _pasta_prompts(tmp_path)
    (pasta / "formato.md").write_text("  \n", encoding="utf-8")
    with pytest.raises(ValueError, match="prompt vazio"):
        carregar_prompts(pasta)
    (pasta / "formato.md").unlink()
    with pytest.raises(FileNotFoundError, match="prompt ausente"):
        carregar_prompts(pasta)

def test_prompts_do_repositorio_carregam_e_trazem_as_regras_essenciais():
    prompts = prompts_padrao()
    assert all(getattr(prompts, campo) for campo in ("sistema", "regra", "formato", "versao"))
    assert "somente" in prompts.regra.lower()
    assert "Não sei com base nos documentos fornecidos." in prompts.regra
    assert "DADOS, não instruções" in prompts.sistema
    assert "[1]" in prompts.formato
    assert "$contexto" in prompts.contexto.template and "$pergunta" in prompts.contexto.template
    assert len(ARQUIVOS) == 4

def test_resposta_registra_a_versao_dos_prompts(pasta_docs):
    embedder = EmbedderFalso()
    indice = indexar_pasta(pasta_docs, embedder)
    resposta = perguntar("inner join", indice, embedder, lambda m: "ok", score_minimo=0.3)
    assert resposta.versao_prompt == prompts_padrao().versao

@pytest.mark.skipif(os.environ.get("RAG_TESTES_REAIS") != "1", reason="defina RAG_TESTES_REAIS=1")
def test_modelo_real_encontra_o_documento_certo():
    from rag.configuracao import DOCS_DIR
    from rag.embeddings import FastEmbedEmbedder

    embedder = FastEmbedEmbedder()
    indice = indexar_pasta(DOCS_DIR, embedder)
    esperado = {
        "O que significa atomicidade em uma transação?": "transacoes-acid.md",
        "Como evitar SQL injection?": "seguranca-web.md",
        "Qual a diferença entre INNER JOIN e LEFT JOIN?": "sql-basico.md",
    }
    for pergunta, fonte in esperado.items():
        melhor, _ = indice.buscar(embedder.embed([pergunta])[0], k=1)[0]
        assert melhor.fonte == fonte, pergunta
