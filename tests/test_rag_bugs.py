import io
import sys
import threading
import time
import types

import pytest

from rag import cli, embeddings, llm
from rag.api import Limites, criar_app
from rag.indice import indexar_pasta
from test_rag import DOC_SQL, EmbedderFalso

PERGUNTA = "o que faz o inner join entre tabelas"


@pytest.fixture
def indice(tmp_path):
    (tmp_path / "sql.md").write_text(DOC_SQL, encoding="utf-8")
    return indexar_pasta(tmp_path, EmbedderFalso())


def montar(indice, llm_falso, **limites):
    return criar_app(indice, EmbedderFalso(), llm_falso, limites=Limites(**limites), score_minimo=0.3)


def perguntar(app, texto=PERGUNTA):
    return app.test_client().post("/ask", json={"pergunta": texto})


class TestRespostaVazia:
    @pytest.mark.parametrize("vazio", ["", "   ", "\n\t"])
    def test_llm_sem_texto_vira_502_e_nao_200_vazio(self, indice, vazio):
        resposta = perguntar(montar(indice, lambda mensagens: vazio))
        assert resposta.status_code == 502
        assert resposta.get_json()["erro"]["codigo"] == "llm_resposta_vazia"


class TestEncoding:
    def test_pergunta_com_surrogate_solto_e_recusada_com_400(self, indice):
        resposta = perguntar(montar(indice, lambda mensagens: "ok"), "oi \ud800 tudo bem")
        assert resposta.status_code == 400
        assert resposta.get_json()["erro"]["codigo"] == "pergunta_invalida"

    def test_saida_do_cli_aguenta_caracteres_fora_do_cp1252(self, monkeypatch):
        bruto = io.BytesIO()
        saida = io.TextIOWrapper(bruto, encoding="cp1252")
        monkeypatch.setattr(sys, "stdout", saida)
        monkeypatch.setattr(sys, "stderr", io.TextIOWrapper(io.BytesIO(), encoding="cp1252"))
        cli.configurar_saida_utf8()
        print("re‑tentar 【1】 não")
        saida.flush()
        assert bruto.getvalue().decode("utf-8").strip() == "re‑tentar 【1】 não"


class TestAdmissaoDeChamadas:
    def test_chamadas_abandonadas_continuam_ocupando_vaga_e_a_quinta_e_recusada(self, indice):
        liberar = threading.Event()

        def llm_travado(mensagens):
            liberar.wait(5)
            return "tarde"

        app = montar(indice, llm_travado, max_concorrencia=2, timeout_llm=0.05)
        try:
            assert perguntar(app).status_code == 504
            assert perguntar(app).status_code == 504
            terceira = perguntar(app)
            assert terceira.status_code == 503
            assert terceira.get_json()["erro"]["codigo"] == "servidor_ocupado"
        finally:
            liberar.set()
        time.sleep(0.2)
        assert perguntar(montar(indice, lambda mensagens: "livre")).status_code == 200

    def test_vaga_volta_depois_que_a_chamada_termina(self, indice):
        app = montar(indice, lambda mensagens: "ok", max_concorrencia=1)
        for _ in range(5):
            assert perguntar(app).status_code == 200


class TestInicializacaoPreguicosa:
    def test_modelo_de_embeddings_e_criado_uma_unica_vez_com_threads_concorrentes(self, monkeypatch):
        criacoes = []

        class ModeloFalso:
            def __init__(self, nome, cache_dir):
                time.sleep(0.05)
                criacoes.append(nome)

            def embed(self, textos):
                return [[1.0, 0.0] for _ in textos]

        monkeypatch.setitem(sys.modules, "fastembed", types.SimpleNamespace(TextEmbedding=ModeloFalso))
        embedder = embeddings.FastEmbedEmbedder(nome="modelo-x")
        threads = [threading.Thread(target=embedder.embed, args=(["a"],)) for _ in range(12)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert criacoes == ["modelo-x"]

    def test_cliente_groq_e_criado_uma_unica_vez_com_threads_concorrentes(self, monkeypatch):
        criacoes = []

        class GroqFalso:
            def __init__(self, **kwargs):
                time.sleep(0.05)
                criacoes.append(1)

        import groq
        monkeypatch.setattr(groq, "Groq", GroqFalso)
        monkeypatch.setattr(llm, "_cliente", None)
        threads = [threading.Thread(target=llm._obter_cliente) for _ in range(12)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(criacoes) == 1
