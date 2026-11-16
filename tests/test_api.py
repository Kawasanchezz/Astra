import json
import logging
import time

import pytest

from rag.api import Limites, criar_app
from rag.indice import indexar_pasta
from rag.llm import LlmNaoConfigurado
from rag.logs import JsonFormatter
from test_rag import DOC_GIT, DOC_SQL, EmbedderFalso

PERGUNTA_SQL = "o que faz o inner join entre tabelas"

@pytest.fixture
def indice(tmp_path):
    (tmp_path / "sql.md").write_text(DOC_SQL, encoding="utf-8")
    (tmp_path / "git.md").write_text(DOC_GIT, encoding="utf-8")
    return indexar_pasta(tmp_path, EmbedderFalso())

class LlmEspiao:
    """LLM falso que guarda o que recebeu; nunca chama a API real."""
    def __init__(self, resposta="Devolve linhas em comum [1]."):
        self.resposta, self.chamadas = resposta, []

    def __call__(self, mensagens):
        self.chamadas.append(mensagens)
        return self.resposta

def _app(indice, llm=None, **opcoes):
    opcoes.setdefault("score_minimo", 0.3)
    return criar_app(indice, EmbedderFalso(), llm or LlmEspiao(), **opcoes)

def _ask(app, corpo=None, **kwargs):
    return app.test_client().post("/ask", json=corpo, **kwargs)

# ---------- /health ----------

def test_health_ok_com_indice(indice):
    resposta = _app(indice).test_client().get("/health")
    assert resposta.status_code == 200
    corpo = resposta.get_json()
    assert corpo["status"] == "ok" and corpo["trechos_indexados"] == len(indice.trechos)
    assert corpo["modelo_embedding"] == "falso-bow-256" and len(corpo["versao_prompt"]) == 10

def test_health_responde_503_sem_indice():
    resposta = _app(None).test_client().get("/health")
    assert resposta.status_code == 503 and resposta.get_json()["status"] == "indice_indisponivel"

# ---------- /ask: caminho feliz ----------

def test_ask_devolve_resposta_fontes_e_id(indice):
    llm = LlmEspiao()
    resposta = _ask(_app(indice, llm), {"pergunta": PERGUNTA_SQL})
    assert resposta.status_code == 200
    corpo = resposta.get_json()
    assert corpo["resposta"] == "Devolve linhas em comum [1]." and corpo["usou_llm"] is True
    assert corpo["fontes"][0]["arquivo"] == "sql.md" and 0 < corpo["fontes"][0]["score"] <= 1
    assert corpo["id"] == resposta.headers["X-Request-ID"]
    assert "inner join" in llm.chamadas[0][1]["content"]

def test_ask_sem_contexto_nao_chama_o_llm(indice):
    llm = LlmEspiao()
    corpo = _ask(_app(indice, llm), {"pergunta": "receita de bolo de cenoura"}).get_json()
    assert corpo["usou_llm"] is False and corpo["fontes"] == [] and llm.chamadas == []

def test_ask_respeita_o_k_enviado(indice):
    llm = LlmEspiao()
    corpo = _ask(_app(indice, llm, score_minimo=0.0), {"pergunta": PERGUNTA_SQL, "k": 1}).get_json()
    assert len(corpo["fontes"]) == 1

def test_request_id_do_cliente_e_reaproveitado_so_se_for_seguro(indice):
    app = _app(indice)
    certo = _ask(app, {"pergunta": PERGUNTA_SQL}, headers={"X-Request-ID": "gateway-123"})
    assert certo.headers["X-Request-ID"] == "gateway-123"
    forjado = 'a"} {"nivel": "ERROR"}'
    suspeito = _ask(app, {"pergunta": PERGUNTA_SQL}, headers={"X-Request-ID": forjado})
    assert suspeito.headers["X-Request-ID"] != forjado and len(suspeito.headers["X-Request-ID"]) == 16

# ---------- /ask: validação ----------

@pytest.mark.parametrize("corpo, status, codigo", [
    ({}, 400, "pergunta_invalida"),
    ({"pergunta": 123}, 400, "pergunta_invalida"),
    ({"pergunta": "   "}, 400, "pergunta_vazia"),
    ({"pergunta": "x" * 501}, 400, "pergunta_longa"),
    ({"pergunta": "ok", "k": 0}, 400, "k_invalido"),
    ({"pergunta": "ok", "k": 11}, 400, "k_invalido"),
    ({"pergunta": "ok", "k": "3"}, 400, "k_invalido"),
    ({"pergunta": "ok", "k": True}, 400, "k_invalido"),
    (["lista"], 400, "json_invalido"),
])
def test_ask_recusa_entrada_invalida_sem_chamar_o_llm(indice, corpo, status, codigo):
    llm = LlmEspiao()
    resposta = _ask(_app(indice, llm), corpo)
    assert resposta.status_code == status and resposta.get_json()["erro"]["codigo"] == codigo
    assert llm.chamadas == []

def test_ask_exige_content_type_json(indice):
    resposta = _app(indice).test_client().post("/ask", data="pergunta=oi", content_type="text/plain")
    assert resposta.status_code == 415 and resposta.get_json()["erro"]["codigo"] == "tipo_invalido"

def test_ask_com_json_quebrado_devolve_400(indice):
    resposta = _app(indice).test_client().post("/ask", data="{quebrado", content_type="application/json")
    assert resposta.status_code == 400 and resposta.get_json()["erro"]["codigo"] == "json_invalido"

def test_corpo_maior_que_o_limite_devolve_413(indice):
    app = _app(indice, limites=Limites(max_corpo=100))
    resposta = _ask(app, {"pergunta": "a" * 300})
    assert resposta.status_code == 413 and resposta.get_json()["erro"]["codigo"] == "corpo_grande"

def test_rota_inexistente_e_metodo_errado_respondem_json(indice):
    cliente = _app(indice).test_client()
    assert cliente.get("/nada").get_json()["erro"]["codigo"] == "nao_encontrado"
    assert cliente.get("/ask").status_code == 405

def test_ask_sem_indice_devolve_503(indice):
    resposta = _ask(_app(None), {"pergunta": PERGUNTA_SQL})
    assert resposta.status_code == 503 and resposta.get_json()["erro"]["codigo"] == "indice_indisponivel"

# ---------- /ask: falhas do LLM ----------

def test_erro_do_llm_vira_502_sem_vazar_detalhe_interno(indice):
    def llm_quebrado(_):
        raise RuntimeError("chave gsk_SEGREDO-INTERNO invalida")
    resposta = _ask(_app(indice, llm_quebrado), {"pergunta": PERGUNTA_SQL})
    assert resposta.status_code == 502 and resposta.get_json()["erro"]["codigo"] == "llm_erro"
    assert "SEGREDO" not in resposta.get_data(as_text=True)

def test_llm_lento_estoura_o_prazo_e_devolve_504(indice):
    def llm_lento(_):
        time.sleep(0.5)
        return "tarde demais"
    app = _app(indice, llm_lento, limites=Limites(timeout_llm=0.05))
    inicio = time.perf_counter()
    resposta = _ask(app, {"pergunta": PERGUNTA_SQL})
    assert resposta.status_code == 504 and resposta.get_json()["erro"]["codigo"] == "llm_timeout"
    assert time.perf_counter() - inicio < 0.4

def test_llm_sem_chave_devolve_503(indice):
    def llm_sem_chave(_):
        raise LlmNaoConfigurado("sem chave")
    resposta = _ask(_app(indice, llm_sem_chave), {"pergunta": PERGUNTA_SQL})
    assert resposta.status_code == 503 and resposta.get_json()["erro"]["codigo"] == "llm_nao_configurado"

def test_falha_fora_do_llm_vira_500_generico(indice):
    class EmbedderQuebrado(EmbedderFalso):
        def embed(self, textos):
            raise ValueError("detalhe-interno-do-embedder")
    app = criar_app(indice, EmbedderQuebrado(), LlmEspiao())
    resposta = _ask(app, {"pergunta": PERGUNTA_SQL})
    assert resposta.status_code == 500 and "detalhe-interno" not in resposta.get_data(as_text=True)

# ---------- autenticação entre serviços ----------

def test_com_token_configurado_o_ask_exige_bearer_e_o_health_continua_publico(indice):
    app = _app(indice, token="segredo-de-teste")
    cliente = app.test_client()
    corpo = {"pergunta": PERGUNTA_SQL}
    assert cliente.post("/ask", json=corpo).status_code == 401
    assert cliente.post("/ask", json=corpo, headers={"Authorization": "Bearer errado"}).status_code == 401
    assert cliente.post("/ask", json=corpo, headers={"Authorization": "Bearer segredo-de-teste"}).status_code == 200
    assert cliente.get("/health").status_code == 200

# ---------- logs estruturados ----------

def test_log_de_requisicao_e_estruturado_e_nao_guarda_a_pergunta(indice, caplog):
    pergunta = "pergunta-confidencial sobre inner join entre tabelas"
    with caplog.at_level(logging.INFO, logger="rag.api"):
        _ask(_app(indice), {"pergunta": pergunta})
    registro = next(r.msg for r in caplog.records if isinstance(r.msg, dict) and r.msg.get("rota") == "/ask")
    assert registro["evento"] == "requisicao" and registro["status"] == 200 and registro["metodo"] == "POST"
    assert registro["pergunta_chars"] == len(pergunta) and registro["usou_llm"] is True
    assert registro["duracao_ms"] >= 0 and registro["id"]
    assert "confidencial" not in json.dumps(registro)

def test_log_de_erro_traz_o_codigo_e_o_tipo_da_excecao(indice, caplog):
    def llm_quebrado(_):
        raise ConnectionError("detalhe")
    with caplog.at_level(logging.INFO, logger="rag.api"):
        _ask(_app(indice, llm_quebrado), {"pergunta": PERGUNTA_SQL})
    registro = next(r.msg for r in caplog.records if isinstance(r.msg, dict) and r.msg.get("rota") == "/ask")
    assert registro["status"] == 502 and registro["erro_codigo"] == "llm_erro"
    assert registro["erro_tipo"] == "ConnectionError" and "detalhe" not in json.dumps(registro)

def test_formatter_gera_uma_linha_json_valida():
    registro = logging.LogRecord("rag.api", logging.INFO, __file__, 1, {"evento": "x", "n": 1}, None, None)
    linha = JsonFormatter().format(registro)
    assert "\n" not in linha
    assert json.loads(linha)["evento"] == "x" and json.loads(linha)["nivel"] == "INFO"
