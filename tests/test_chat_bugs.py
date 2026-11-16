import json
import logging
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import groq
import httpx
import pytest

import config
import main
from core.seguranca import mascarar_segredos
from services import ia_service

RAIZ = Path(__file__).resolve().parent.parent
PEDIDO = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")


def resposta_llm(texto):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=texto))])


class ClienteFalso:
    def __init__(self, comportamento):
        self.chamadas = []

        def create(**kwargs):
            self.chamadas.append(kwargs)
            return comportamento(kwargs)

        self.chat = SimpleNamespace(completions=SimpleNamespace(create=create))


def erro_http(classe, status):
    resposta = httpx.Response(status, request=PEDIDO)
    return classe("erro do provedor com detalhe-interno-secreto", response=resposta, body=None)


@pytest.fixture
def usar_llm(monkeypatch):
    main.limiter.reset()

    def instalar(comportamento):
        cliente = ClienteFalso(comportamento)
        monkeypatch.setattr(ia_service, "client", cliente)
        return cliente

    def proibido(_):
        raise AssertionError("LLM real não pode ser chamado")

    monkeypatch.setattr(ia_service, "client", ClienteFalso(proibido))
    return instalar


def perguntar(corpo):
    try:
        enviado = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
    except UnicodeEncodeError:
        enviado = json.dumps(corpo).encode("ascii")
    return main.app.test_client().post("/chat", data=enviado, content_type="application/json")


MENSAGEM = {"mensagem": "Explique listas em Python"}


class TestRegexQuadratica:
    @pytest.mark.parametrize("padrao", ["a.", "a-", "a+"])
    def test_mascarar_segredos_e_linear_em_entrada_longa(self, padrao):
        texto = padrao * 4000
        inicio = time.perf_counter()
        mascarar_segredos(texto)
        assert time.perf_counter() - inicio < 0.25

    def test_continua_mascarando_a_senha_de_uma_url(self):
        texto, achou = mascarar_segredos("conecte em postgres://usuario:senha-secreta@banco.local/app")
        assert achou and "senha-secreta" not in texto and "postgres://usuario:" in texto


class TestSurrogates:
    def test_sanitizar_remove_surrogate_solto(self):
        assert ia_service.sanitizar_input("a\ud800b\udfffc") == "abc"

    def test_mensagem_com_surrogate_chega_ao_llm_codificavel(self, usar_llm):
        cliente = usar_llm(lambda kw: resposta_llm("ok"))
        resposta = perguntar({"mensagem": "Explique listas \ud800 em Python"})
        assert resposta.status_code == 200
        for mensagem in cliente.chamadas[0]["messages"]:
            mensagem["content"].encode("utf-8")


class TestFalhasDoLlm:
    @pytest.mark.parametrize("erro, status, motivo", [
        (groq.APITimeoutError(request=PEDIDO), 504, "timeout"),
        (erro_http(groq.RateLimitError, 429), 503, "limite_do_provedor"),
        (groq.APIConnectionError(request=PEDIDO), 502, "conexao"),
        (erro_http(groq.AuthenticationError, 401), 500, "credencial_recusada"),
        (erro_http(groq.PermissionDeniedError, 403), 500, "credencial_recusada"),
        (erro_http(groq.InternalServerError, 500), 502, "erro_do_provedor"),
        (RuntimeError("detalhe-interno-secreto"), 500, "inesperado"),
    ])
    def test_cada_falha_vira_status_proprio_sem_vazar_detalhe(self, usar_llm, erro, status, motivo, caplog):
        def falhar(_):
            raise erro
        usar_llm(falhar)
        with caplog.at_level(logging.ERROR):
            resposta = perguntar(MENSAGEM)
        assert resposta.status_code == status
        corpo = resposta.get_json()
        assert list(corpo) == ["erro"] and "detalhe-interno-secreto" not in resposta.get_data(as_text=True)
        registro = next(r.getMessage() for r in caplog.records if "Falha na LLM" in r.getMessage())
        assert f"motivo={motivo}" in registro and "detalhe-interno-secreto" not in registro

    def test_erro_nao_e_devolvido_como_resposta_do_assistente(self, usar_llm):
        usar_llm(lambda kw: (_ for _ in ()).throw(groq.APITimeoutError(request=PEDIDO)))
        corpo = perguntar(MENSAGEM).get_json()
        assert "resposta" not in corpo and corpo["erro"]

    def test_vaga_de_concorrencia_e_devolvida_depois_de_falhas(self, usar_llm):
        usar_llm(lambda kw: (_ for _ in ()).throw(RuntimeError("x")))
        for _ in range(10):
            perguntar(MENSAGEM)
        assert main._vagas_ia._value == config.MAX_CONCURRENT_REQUESTS


class TestRespostaVazia:
    @pytest.mark.parametrize("conteudo", [None, "", "   \n"])
    def test_conteudo_vazio_vira_502(self, usar_llm, conteudo):
        usar_llm(lambda kw: resposta_llm(conteudo))
        resposta = perguntar(MENSAGEM)
        assert resposta.status_code == 502 and "nao devolveu resposta" in resposta.get_json()["erro"]

    def test_lista_de_choices_vazia_vira_502(self, usar_llm):
        usar_llm(lambda kw: SimpleNamespace(choices=[]))
        assert perguntar(MENSAGEM).status_code == 502

    def test_resposta_normal_continua_200(self, usar_llm):
        usar_llm(lambda kw: resposta_llm("Listas são mutáveis."))
        resposta = perguntar(MENSAGEM)
        assert resposta.status_code == 200 and resposta.get_json()["resposta"] == "Listas são mutáveis."


class TestPrazos:
    @pytest.mark.parametrize("bruto, extras, total, esperado", [
        (30, 1, 25, 12), (30, 0, 25, 25), (10, 1, 25, 10), (30, 3, 25, 6), (30, 3, 8, 5),
    ])
    def test_prazo_por_tentativa_cabe_no_prazo_total(self, bruto, extras, total, esperado):
        assert config.calcular_timeout_llm(bruto, extras, total) == esperado

    def test_pior_caso_da_configuracao_cabe_na_funcao_da_vercel(self):
        vercel = json.loads((RAIZ / "vercel.json").read_text(encoding="utf-8"))
        limite = vercel["functions"]["app.py"]["maxDuration"]
        pior_caso = config.GROQ_TIMEOUT * (config.GROQ_MAX_RETRIES + 1)
        assert pior_caso <= config.PRAZO_TOTAL_LLM < limite

    def test_chamada_usa_o_prazo_calculado(self, usar_llm):
        cliente = usar_llm(lambda kw: resposta_llm("ok"))
        perguntar(MENSAGEM)
        assert cliente.chamadas[0]["timeout"] == config.GROQ_TIMEOUT


class TestTamanhoEmBytes:
    def test_conversa_longa_em_chines_nao_estoura_o_limite_do_corpo(self, usar_llm):
        usar_llm(lambda kw: resposta_llm("好"))
        historico = [{"role": "user" if i % 2 == 0 else "assistant", "content": "你" * 1000} for i in range(10)]
        corpo = {"mensagem": "好" * config.MAX_INPUT_LENGTH, "historico": historico}
        assert len(json.dumps(corpo, ensure_ascii=False).encode("utf-8")) > 32 * 1024
        assert perguntar(corpo).status_code == 200

    def test_corpo_gigante_continua_recusado(self, usar_llm):
        usar_llm(lambda kw: resposta_llm("ok"))
        resposta = perguntar({"mensagem": "oi", "historico": [{"role": "user", "content": "x" * 300_000}]})
        assert resposta.status_code == 413


class TestConcorrencia:
    def test_respostas_simultaneas_nao_se_misturam_entre_usuarios(self, usar_llm):
        def eco(kwargs):
            time.sleep(0.05)
            return resposta_llm("ECO:" + kwargs["messages"][-1]["content"])

        usar_llm(eco)
        resultados = {}

        def usuario(n):
            corpo = {"mensagem": f"pergunta única número {n} sobre listas", "historico": [
                {"role": "user", "content": f"histórico do usuário {n}"}]}
            resultados[n] = perguntar(corpo).get_json()["resposta"]

        threads = [threading.Thread(target=usuario, args=(n,)) for n in range(config.MAX_CONCURRENT_REQUESTS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        esperado = {n: f"ECO:pergunta única número {n} sobre listas" for n in range(config.MAX_CONCURRENT_REQUESTS)}
        assert resultados == esperado
