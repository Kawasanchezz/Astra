import json
from pathlib import Path

import pytest

from rag.avaliacao import (Pergunta, avaliar, avaliar_pergunta, carregar_perguntas, contem_termos,
                           eh_recusa, resumir)
from rag.consulta import SEM_CONTEXTO
from rag.indice import indexar_pasta
from rag.prompts import prompts_padrao
from test_rag import DOC_GIT, DOC_SQL, EmbedderFalso

RAIZ = Path(__file__).resolve().parent.parent

@pytest.fixture
def ambiente(tmp_path):
    (tmp_path / "sql.md").write_text(DOC_SQL, encoding="utf-8")
    (tmp_path / "git.md").write_text(DOC_GIT, encoding="utf-8")
    embedder = EmbedderFalso()
    return indexar_pasta(tmp_path, embedder), embedder

def _avaliar(item, ambiente, llm):
    indice, embedder = ambiente
    return avaliar_pergunta(item, indice, embedder, llm, k=2, score_minimo=0.3, prompts=prompts_padrao())

JOIN = Pergunta("a", "o que faz o inner join entre tabelas", "x", "sql.md", [["correspond"]])
FORA = Pergunta("b", "receita de bolo de cenoura", "recusar", None, [])

# ---------- perguntas do repositório ----------

def test_arquivo_de_perguntas_esta_integro():
    perguntas = carregar_perguntas(RAIZ / "avaliacao" / "perguntas.json")
    assert len(perguntas) == 10
    assert len({p.id for p in perguntas}) == 10
    assert sum(not p.deve_responder for p in perguntas) >= 2
    existentes = {f.name for f in (RAIZ / "docs" / "estudo").glob("*.md")}
    assert all(p.fonte in existentes for p in perguntas if p.deve_responder)
    assert all(p.termos for p in perguntas if p.deve_responder)

# ---------- helpers ----------

def test_eh_recusa_reconhece_as_duas_recusas_e_nao_confunde_resposta_normal():
    assert eh_recusa("Não sei com base nos documentos fornecidos.")
    assert eh_recusa(SEM_CONTEXTO)
    assert eh_recusa("Não sei. [1]")
    assert not eh_recusa("O inner join devolve linhas em comum [1].")

def test_contem_termos_ignora_acento_e_caixa_e_exige_todos_os_grupos():
    texto = "A ATOMICIDADE garante o rollback."
    assert contem_termos(texto, [["atomicidade"], ["rollback", "desfaz"]])
    assert not contem_termos(texto, [["atomicidade"], ["isolamento"]])
    assert contem_termos("Imutável", [["imutavel"]])

# ---------- avaliação ----------

def test_aprova_quando_cita_o_trecho_do_documento_certo(ambiente):
    r = _avaliar(JOIN, ambiente, lambda m: "Devolve as linhas com correspondência [1].")
    assert r.aprovado and r.citou_fonte_certa and r.formato_citacao_ok and r.fonte_em_primeiro
    assert r.motivos_de_falha == []

def test_reprova_quando_nao_cita_nenhum_trecho(ambiente):
    r = _avaliar(JOIN, ambiente, lambda m: "Devolve as linhas com correspondência.")
    assert not r.aprovado and not r.citou_fonte_certa
    assert "não citou o trecho do documento certo" in r.motivos_de_falha

def test_reprova_citacao_de_trecho_inexistente(ambiente):
    r = _avaliar(JOIN, ambiente, lambda m: "Devolve as linhas com correspondência [9].")
    assert r.citacao_invalida and not r.aprovado

def test_citacao_com_colchetes_largos_conta_mas_nao_esta_no_formato(ambiente):
    r = _avaliar(JOIN, ambiente, lambda m: "Devolve as linhas com correspondência 【1】.")
    assert r.citou_fonte_certa and not r.formato_citacao_ok

def test_reprova_quando_faltam_os_termos_esperados(ambiente):
    r = _avaliar(JOIN, ambiente, lambda m: "Junta tabelas [1].")
    assert r.citou_fonte_certa and not r.termos_ok and not r.aprovado

def test_reprova_quando_recusa_pergunta_que_os_documentos_cobrem(ambiente):
    r = _avaliar(JOIN, ambiente, lambda m: "Não sei com base nos documentos fornecidos.")
    assert r.recusou and not r.aprovado
    assert "recusou uma pergunta que os documentos cobrem" in r.motivos_de_falha

def test_pergunta_fora_do_corpus_aprova_quando_recusa_sem_chamar_o_llm(ambiente):
    def llm_proibido(_):
        raise AssertionError("não deveria chamar o LLM")
    r = _avaliar(FORA, ambiente, llm_proibido)
    assert r.aprovado and r.recusou and r.recuperados == []

def test_pergunta_fora_do_corpus_reprova_quando_o_modelo_responde_mesmo_assim(ambiente):
    forcada = Pergunta("c", "o que faz o inner join entre tabelas", "recusar", None, [])
    r = _avaliar(forcada, ambiente, lambda m: "É uma junção [1].")
    assert not r.aprovado
    assert "respondeu algo que os documentos não cobrem" in r.motivos_de_falha

def test_resumo_conta_cada_metrica_separadamente(ambiente):
    indice, embedder = ambiente
    resultados = avaliar([JOIN, FORA], indice, embedder, lambda m: "Devolve linhas com correspondência [1].",
                         k=2, score_minimo=0.3)
    resumo = resumir(resultados)
    assert resumo["aprovadas"] == 2
    assert resumo["responder"] == {
        "total": 1, "recuperou_documento_certo": 1, "documento_certo_em_primeiro": 1, "citou_fonte_certa": 1,
        "citacao_no_formato": 1, "citacao_invalida": 0, "termos_esperados": 1, "recusou_indevidamente": 0}
    assert resumo["recusar"] == {"total": 1, "recusou_corretamente": 1}

def test_resultado_e_serializavel_em_json(ambiente):
    from dataclasses import asdict
    r = _avaliar(JOIN, ambiente, lambda m: "Devolve linhas com correspondência [1].")
    assert json.loads(json.dumps(asdict(r), ensure_ascii=False))["id"] == "a"
