import logging
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

import config
import main
from rag import llm
from rag.api import criar_app
from services import ia_service
from apoio import ClienteFalso, resposta_llm
from test_rag import EmbedderFalso

RAIZ = Path(__file__).resolve().parent.parent
CHAVE_FALSA = "chave-falsa-de-teste"
GSK = "gsk_" + "A1b2C3d4" * 6
PADROES_DE_SEGREDO = [
    re.compile(r"\bgsk_[A-Za-z0-9]{20,}"),
    re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:ghp|gho|ghs|ghu)_[A-Za-z0-9_]{30,}"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


def arquivos_rastreados():
    try:
        saida = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
                               check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git indisponível")
    return [RAIZ / linha for linha in saida.splitlines()
            if linha and "/vendor/" not in linha and not linha.endswith((".png", ".ico", ".woff2"))]


class TestChaveSoPorAmbiente:
    def test_nenhum_arquivo_rastreado_tem_credencial_embutida(self):
        achados = []
        for arquivo in arquivos_rastreados():
            if arquivo.name.startswith("test_") and arquivo.suffix == ".py":
                continue
            texto = arquivo.read_text(encoding="utf-8", errors="ignore")
            achados += [f"{arquivo.relative_to(RAIZ)}: {p.pattern[:20]}" for p in PADROES_DE_SEGREDO if p.search(texto)]
        assert achados == []

    def test_a_chave_vem_do_ambiente(self):
        assert config.GROQ_API_KEY == CHAVE_FALSA

    def test_arquivos_env_reais_nao_sao_rastreados(self):
        rastreados = [a.name for a in arquivos_rastreados()]
        assert not [n for n in rastreados if n == ".env" or (n.startswith(".env.") and not n.endswith(".example"))]

    @pytest.mark.parametrize("ignore", [".gitignore", ".dockerignore", ".vercelignore"])
    def test_arquivos_de_ignore_cobrem_o_env(self, ignore):
        linhas = {linha.strip() for linha in (RAIZ / ignore).read_text(encoding="utf-8").splitlines()}
        assert ".env" in linhas or "**/.env" in linhas
        assert ".env.*" in linhas or "**/.env.*" in linhas

    def test_git_ignora_o_env_do_servidor(self):
        resultado = subprocess.run(["git", "check-ignore", "-q", "servidor/.env"], cwd=RAIZ)
        assert resultado.returncode == 0

    def test_exemplos_de_env_trazem_so_placeholder_ou_vazio(self):
        for arquivo in (".env.example", "servidor/.env.example"):
            for linha in (RAIZ / arquivo).read_text(encoding="utf-8").splitlines():
                nome, _, valor = linha.partition("=")
                if nome.strip() in ("GROQ_API_KEY", "RAG_API_TOKEN"):
                    assert valor.strip() in ("", config.CHAVE_PLACEHOLDER), (arquivo, nome)

    def test_dockerfiles_e_compose_nao_embutem_segredo(self):
        for arquivo in ("Dockerfile.rag", "ai-gateway-java/Dockerfile"):
            texto = (RAIZ / arquivo).read_text(encoding="utf-8")
            assert not re.search(r"^\s*(ENV|ARG)\s+\S*(KEY|TOKEN|SECRET|PASSWORD)", texto, re.M | re.I), arquivo
        for linha in (RAIZ / "docker-compose.yml").read_text(encoding="utf-8").splitlines():
            if re.search(r"(KEY|TOKEN):", linha):
                assert "${" in linha, linha


class TestPlaceholderDaChave:
    def test_placeholder_e_vazio_nao_contam_como_configurada(self, monkeypatch):
        for valor in ("", config.CHAVE_PLACEHOLDER):
            monkeypatch.setattr(config, "GROQ_API_KEY", valor)
            assert config.chave_groq_configurada() is False
        monkeypatch.setattr(config, "GROQ_API_KEY", GSK)
        assert config.chave_groq_configurada() is True

    def test_health_nao_diz_que_esta_configurada_com_o_placeholder(self, monkeypatch):
        monkeypatch.setattr(config, "GROQ_API_KEY", config.CHAVE_PLACEHOLDER)
        corpo = main.app.test_client().get("/health").get_json()
        assert corpo["ia_configurada"] is False

    def test_rag_recusa_o_placeholder_como_se_nao_houvesse_chave(self, monkeypatch):
        monkeypatch.setattr(config, "GROQ_API_KEY", config.CHAVE_PLACEHOLDER)
        with pytest.raises(llm.LlmNaoConfigurado):
            llm.llm_groq([{"role": "user", "content": "oi"}])

    def test_health_nunca_devolve_o_valor_da_chave(self):
        resposta = main.app.test_client().get("/health")
        assert CHAVE_FALSA not in resposta.get_data(as_text=True)


class TestChaveNaoVaiParaLogsNemRespostas:
    def test_erro_do_provedor_com_a_chave_na_mensagem_nao_vaza(self, monkeypatch, caplog):
        main.limiter.reset()
        pedido = httpx.Request("POST", "https://api.groq.com/x")

        def falhar(_):
            raise RuntimeError(f"Incorrect API key provided: {CHAVE_FALSA}")

        monkeypatch.setattr(ia_service, "client", ClienteFalso(falhar))
        with caplog.at_level(logging.DEBUG):
            resposta = main.app.test_client().post("/chat", json={"mensagem": "Explique listas em Python"})
        assert resposta.status_code == 500 and pedido
        assert CHAVE_FALSA not in resposta.get_data(as_text=True)
        assert all(CHAVE_FALSA not in r.getMessage() for r in caplog.records)

    def test_chave_digitada_pelo_usuario_e_mascarada_antes_do_llm_e_fora_dos_logs(self, monkeypatch, caplog):
        main.limiter.reset()
        cliente = ClienteFalso(lambda kw: resposta_llm("ok"))
        monkeypatch.setattr(ia_service, "client", cliente)
        historico = [{"role": "user", "content": f"minha chave antiga era {GSK}"}]
        with caplog.at_level(logging.DEBUG):
            main.app.test_client().post("/chat", json={
                "mensagem": f"revise: GROQ_API_KEY={GSK} no meu código", "historico": historico})
        enviado = " ".join(m["content"] for m in cliente.chamadas[0]["messages"])
        assert GSK not in enviado and "gsk_****" in enviado
        assert all(GSK not in r.getMessage() for r in caplog.records)

    def test_resposta_do_modelo_com_chave_e_mascarada_antes_de_chegar_ao_usuario(self, monkeypatch):
        main.limiter.reset()
        monkeypatch.setattr(ia_service, "client", ClienteFalso(lambda kw: resposta_llm(f"Use a chave {GSK} no código")))
        corpo = main.app.test_client().post("/chat", json={"mensagem": "Como configuro a Groq?"}).get_json()
        assert GSK not in corpo["resposta"] and "gsk_****" in corpo["resposta"]

    def test_logs_de_debug_do_sdk_ficam_desligados_mesmo_com_groq_log_debug(self, caplog):
        sdk = logging.getLogger("groq")
        sdk.setLevel(logging.DEBUG)
        config.restringir_logs_de_terceiros()
        with caplog.at_level(logging.DEBUG):
            logging.getLogger("groq._base_client").debug("Request options: %s", GSK)
        assert all(GSK not in r.getMessage() for r in caplog.records)

    def test_token_entre_servicos_nao_aparece_nos_logs_da_api_do_rag(self, caplog):
        app = criar_app(SimpleNamespace(trechos=[], buscar=lambda *a: []), EmbedderFalso(), lambda m: "ok",
                        token="token-secreto-123")
        with caplog.at_level(logging.DEBUG):
            app.test_client().post("/ask", json={"pergunta": "oi"}, headers={"Authorization": "Bearer errado-456"})
            ok = {"Authorization": "Bearer token-secreto-123"}
            app.test_client().post("/ask", json={"pergunta": "oi"}, headers=ok)
        texto = " ".join(str(r.msg) + r.getMessage() for r in caplog.records)
        assert "token-secreto-123" not in texto and "errado-456" not in texto


class TestChaveNaoChegaAoNavegador:
    def test_nenhum_arquivo_do_frontend_contem_a_chave(self):
        cliente = main.app.test_client()
        main.limiter.reset()
        servidos = 0
        for arquivo in (RAIZ / "landing-page").rglob("*"):
            if not arquivo.is_file() or arquivo.suffix in (".woff2", ".png", ".ico"):
                continue
            caminho = "/" + arquivo.relative_to(RAIZ / "landing-page").as_posix()
            resposta = cliente.get(caminho)
            if resposta.status_code == 200:
                servidos += 1
                texto = resposta.get_data(as_text=True)
                assert CHAVE_FALSA not in texto and "GROQ_API_KEY" not in texto, caminho
            main.limiter.reset()
        assert servidos > 10

    @pytest.mark.parametrize("caminho", ["/.env", "/servidor/.env", "/../servidor/.env", "/%2e%2e/servidor/.env",
                                         "/.git/config", "/config.py", "/servidor/config.py"])
    def test_arquivos_sensiveis_nao_sao_servidos(self, caminho):
        main.limiter.reset()
        resposta = main.app.test_client().get(caminho)
        assert resposta.status_code in (400, 404)
        assert CHAVE_FALSA not in resposta.get_data(as_text=True)
