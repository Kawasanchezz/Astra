import logging

import pytest

import main
from apoio import perguntar, resposta_llm
from core.logs import FiltroDeLog, mascarar, novo_id

CHAVE = "gsk_AbCdEf0123456789XyZ"


@pytest.mark.parametrize("texto", [
    f"falha com chave {CHAVE}",
    "Authorization: Bearer abc123.def456-ghi789",
    "token sk-proj-abcdefghijklmnop1234",
    "usuario maria.silva@exemplo.com.br reclamou",
])
def test_mascarar_remove_segredos_e_dados_pessoais(texto):
    saida = mascarar(texto)
    assert "[oculto]" in saida
    for pedaco in (CHAVE, "abc123.def456", "abcdefghijklmnop", "maria.silva", "@exemplo"):
        assert pedaco not in saida


def test_mascarar_nao_mexe_em_texto_comum():
    assert mascarar("chat ip=203.0.113.x msg=12ch hist=0msg") == "chat ip=203.0.113.x msg=12ch hist=0msg"


def test_filtro_mascara_argumentos_do_log_e_campos_de_dict():
    registro = logging.LogRecord("t", logging.ERROR, "f", 1, "falha %s", (CHAVE,), None)
    assert FiltroDeLog().filter(registro)
    assert CHAVE not in registro.getMessage()

    registro = logging.LogRecord("t", logging.INFO, "f", 1, {"erro": f"x {CHAVE}", "status": 200}, None, None)
    FiltroDeLog().filter(registro)
    assert CHAVE not in registro.msg["erro"] and registro.msg["status"] == 200


@pytest.mark.parametrize("recebido", ["abc\n", "abcdefgh\nINFO falso", "curto", "a" * 65, "x y z w q r s t", ""])
def test_id_do_cliente_perigoso_e_descartado(recebido):
    assert novo_id(recebido) != recebido
    assert len(novo_id(recebido)) == 16


def test_id_do_cliente_valido_e_mantido():
    assert novo_id("req-12345678") == "req-12345678"


def test_toda_resposta_tem_id_e_o_id_chega_ao_log(usar_llm, caplog):
    usar_llm(lambda _: resposta_llm("ok"))
    caplog.set_level(logging.INFO)
    r = main.app.test_client().post("/chat", json={"mensagem": "oi"}, headers={"X-Request-ID": "corr-abcdef12"})
    assert r.headers["X-Request-ID"] == "corr-abcdef12"
    assert r.status_code == 200
    assert any(getattr(x, "id", None) == "corr-abcdef12" for x in caplog.records)


def test_erro_inesperado_devolve_id_sem_detalhe_e_loga_com_o_mesmo_id(monkeypatch, caplog):
    def quebra(*_a, **_k):
        raise RuntimeError(f"explodiu com {CHAVE} em C:\\segredo\\arquivo.py")

    monkeypatch.setattr(main, "obter_resposta_ia", quebra)
    app = main.app
    app.config["PROPAGATE_EXCEPTIONS"] = False
    caplog.set_level(logging.INFO)
    r = app.test_client().post("/chat", json={"mensagem": "oi"}, headers={"X-Request-ID": "corr-erro-0001"})
    corpo = r.get_data(as_text=True)
    assert r.status_code == 500
    assert r.get_json()["id"] == "corr-erro-0001"
    assert CHAVE not in corpo and "Traceback" not in corpo and "segredo" not in corpo
    erros = [x for x in caplog.records if x.levelno >= logging.ERROR]
    assert erros and all(x.id == "corr-erro-0001" for x in erros)
    assert all("Traceback" not in x.getMessage() and CHAVE not in x.getMessage() for x in erros)
    assert not any(x.exc_info for x in erros)


def test_erro_do_provedor_nao_vaza_chave_nem_texto_do_usuario_no_log(usar_llm, caplog):
    def quebra(_):
        raise RuntimeError(f"falha {CHAVE}")

    usar_llm(quebra)
    caplog.set_level(logging.INFO)
    perguntar({"mensagem": "meu cpf e 123.456.789-09 e email joao@x.com"})
    texto = "\n".join(x.getMessage() for x in caplog.records)
    assert CHAVE not in texto
    assert "123.456.789-09" not in texto and "joao@x.com" not in texto


def test_erros_http_tambem_trazem_id():
    r = main.app.test_client().post("/chat", data="{", content_type="application/json")
    assert r.status_code == 400
    assert r.get_json()["id"] == r.headers["X-Request-ID"]
    r = main.app.test_client().get("/nao-existe-xyz")
    assert r.status_code == 404 and r.get_json()["id"]
