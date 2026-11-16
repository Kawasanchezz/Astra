import re
from pathlib import Path

import pytest
from flask import session

import config
import main

RAIZ = Path(__file__).resolve().parent.parent
PRODUCAO = {"APP_ENV": "production", "FORCE_HTTPS": "false", "ALLOWED_ORIGINS": "https://astra.example"}
CHAVE_FORTE = "7f3a9c1e5b2d4f60a8c7e1d93b5f2a4c6e8d0b1a3c5e7f9a2b4d6c8e0f1a3b5c"

ROTAS = ["/", "/app", "/css/style.css", "/js/vendor/three/three.module.js", "/models", "/limites", "/health",
         "/naoexiste", "/.env", "/servidor/config.py"]


def cabecalhos_de(resposta):
    return {nome.lower(): valor for nome, valor in resposta.headers.items()}


class TestCabecalhosDeSeguranca:
    @pytest.mark.parametrize("rota", ROTAS)
    def test_toda_resposta_traz_os_cabecalhos(self, rota):
        main.limiter.reset()
        h = cabecalhos_de(main.app.test_client().get(rota))
        assert h["x-content-type-options"] == "nosniff"
        assert h["x-frame-options"] == "DENY"
        assert h["referrer-policy"] == "no-referrer"
        assert "microphone=(self)" in h["permissions-policy"] and "camera=()" in h["permissions-policy"]
        assert h["cross-origin-opener-policy"] == "same-origin"
        assert h["cross-origin-resource-policy"] == "same-origin"

    @pytest.mark.parametrize("metodo, rota", [("post", "/chat"), ("get", "/chat"), ("put", "/chat"), ("get", "/xyz")])
    def test_respostas_de_erro_tambem_trazem_os_cabecalhos(self, metodo, rota):
        main.limiter.reset()
        h = cabecalhos_de(getattr(main.app.test_client(), metodo)(rota))
        assert h["x-content-type-options"] == "nosniff" and h["x-frame-options"] == "DENY"
        assert "content-security-policy" in h

    def test_csp_e_restritiva(self):
        csp = cabecalhos_de(main.app.test_client().get("/"))["content-security-policy"]
        diretivas = {parte.split()[0]: parte.split()[1:] for parte in csp.split("; ")}
        assert diretivas["default-src"] == ["'self'"] and diretivas["script-src"] == ["'self'"]
        assert diretivas["style-src"] == ["'self'"] and diretivas["connect-src"] == ["'self'"]
        assert diretivas["object-src"] == ["'none'"] and diretivas["base-uri"] == ["'self'"]
        assert diretivas["form-action"] == ["'self'"] and diretivas["frame-ancestors"] == ["'none'"]
        assert diretivas["frame-src"] == ["'none'"] and diretivas["worker-src"] == ["'none'"]
        assert diretivas["img-src"] == ["'self'", "data:"]
        assert "unsafe-inline" not in csp and "unsafe-eval" not in csp and "*" not in csp

    def test_hsts_so_em_producao(self, recarregar):
        assert "strict-transport-security" not in cabecalhos_de(main.app.test_client().get("/health"))
        app = recarregar(**PRODUCAO)
        h = cabecalhos_de(app.test_client().get("/health"))
        assert h["strict-transport-security"] == "max-age=31536000; includeSubDomains"
        assert h["content-security-policy"].endswith("upgrade-insecure-requests")

    def test_a_api_do_rag_tambem_traz_cabecalhos_defensivos(self):
        from apoio import ClienteFalso  # noqa: F401
        from rag.api import criar_app
        from test_rag import EmbedderFalso

        app = criar_app(None, EmbedderFalso(), lambda m: "ok")
        h = cabecalhos_de(app.test_client().get("/health"))
        assert h["x-content-type-options"] == "nosniff" and h["x-frame-options"] == "DENY"
        assert h["cache-control"] == "no-store" and "default-src 'none'" in h["content-security-policy"]


class TestPoliticaDeCache:
    def test_html_e_revalidado(self):
        for rota in ("/", "/app"):
            assert cabecalhos_de(main.app.test_client().get(rota))["cache-control"] == "no-cache"

    def test_estatico_versionado_e_imutavel_e_sem_versao_e_revalidado(self):
        cliente = main.app.test_client()
        versionado = cabecalhos_de(cliente.get("/css/style.css?v=28"))["cache-control"]
        assert versionado == "public, max-age=31536000, immutable"
        assert cabecalhos_de(cliente.get("/css/style.css"))["cache-control"] == "no-cache"

    def test_revalidacao_condicional_devolve_304(self):
        cliente = main.app.test_client()
        etag = cliente.get("/css/style.css").headers["ETag"]
        resposta = cliente.get("/css/style.css", headers={"If-None-Match": etag})
        assert resposta.status_code == 304 and cabecalhos_de(resposta)["cache-control"] == "no-cache"

    @pytest.mark.parametrize("rota", ["/models", "/limites", "/health", "/naoexiste", "/.env"])
    def test_json_e_erros_nunca_sao_guardados(self, rota):
        main.limiter.reset()
        assert cabecalhos_de(main.app.test_client().get(rota))["cache-control"] == "no-store"

    def test_resposta_do_chat_nunca_e_guardada(self, usar_llm):
        from apoio import perguntar, resposta_llm
        usar_llm(lambda kw: resposta_llm("ok"))
        assert cabecalhos_de(perguntar({"mensagem": "Explique listas"}))["cache-control"] == "no-store"


class TestCors:
    def test_origem_permitida_recebe_exatamente_a_propria_origem(self):
        h = cabecalhos_de(main.app.test_client().options(
            "/chat", headers={"Origin": "http://localhost:5000", "Access-Control-Request-Method": "POST",
                              "Access-Control-Request-Headers": "content-type"}))
        assert h["access-control-allow-origin"] == "http://localhost:5000"
        assert "access-control-allow-credentials" not in h and h["vary"].lower().count("origin") >= 1
        assert set(re.split(r",\s*", h["access-control-allow-methods"])) == {"GET", "POST", "OPTIONS"}

    @pytest.mark.parametrize("origem", ["https://evil.test", "null", "http://localhost:5001", "http://localhost.evil.test"])
    def test_origem_nao_listada_nao_recebe_permissao(self, origem):
        h = cabecalhos_de(main.app.test_client().options(
            "/chat", headers={"Origin": origem, "Access-Control-Request-Method": "POST"}))
        assert "access-control-allow-origin" not in h

    def test_cabecalho_nao_listado_no_preflight_nao_e_permitido(self):
        h = cabecalhos_de(main.app.test_client().options(
            "/chat", headers={"Origin": "http://localhost:5000", "Access-Control-Request-Method": "POST",
                              "Access-Control-Request-Headers": "x-segredo, authorization"}))
        assert "authorization" not in h.get("access-control-allow-headers", "").lower()

    def test_origens_invalidas_do_ambiente_sao_descartadas(self):
        bruto = ["*", "null", "https://ok.example/", "https://ok.example", "https://x.example/caminho",
                 "javascript:alert(1)", "ftp://x.example", "https://u:p@x.example", "", "http://localhost:5000?a=1"]
        assert config.normalizar_origens(bruto) == ["https://ok.example"]

    def test_curinga_no_ambiente_nao_abre_o_cors(self, recarregar):
        app = recarregar(ALLOWED_ORIGINS="*,null")
        assert main.ALLOWED_ORIGINS == []
        h = cabecalhos_de(app.test_client().options(
            "/chat", headers={"Origin": "https://evil.test", "Access-Control-Request-Method": "POST"}))
        assert "access-control-allow-origin" not in h


class TestOrigemEmProducao:
    def enviar(self, app, origem, tipo="application/json", corpo=b"{}"):
        cabecalhos = {"Origin": origem} if origem is not None else {}
        return app.test_client().post("/chat", data=corpo, content_type=tipo, headers=cabecalhos)

    def test_origem_permitida_passa_pela_checagem(self, recarregar):
        app = recarregar(**PRODUCAO)
        assert self.enviar(app, "https://astra.example").status_code == 400

    @pytest.mark.parametrize("origem", ["https://evil.test", "null", "https://astra.example.evil.test",
                                        "http://astra.example", None])
    def test_origem_estranha_ou_ausente_e_recusada_com_403(self, recarregar, origem):
        app = recarregar(**PRODUCAO)
        assert self.enviar(app, origem).status_code == 403

    def test_mesma_origem_do_proprio_site_e_aceita(self, recarregar):
        app = recarregar(**PRODUCAO)
        resposta = app.test_client().post("/chat", data=b"{}", content_type="application/json",
                                          base_url="https://outro.example", headers={"Origin": "https://outro.example"})
        assert resposta.status_code == 400

    def test_post_simples_entre_sites_nao_vira_json(self, recarregar):
        app = recarregar(**PRODUCAO)
        resposta = self.enviar(app, "https://astra.example", tipo="text/plain", corpo=b'{"mensagem":"oi"}')
        assert resposta.status_code == 400

    def test_debug_do_flask_e_ignorado_em_producao(self, recarregar):
        recarregar(**PRODUCAO, FLASK_DEBUG="true")
        assert config.FLASK_DEBUG is False and main.FLASK_DEBUG is False


class TestCookiesESessao:
    def test_o_app_nao_define_cookies(self):
        cliente = main.app.test_client()
        for rota in ("/", "/app", "/health", "/css/style.css"):
            main.limiter.reset()
            assert cabecalhos_de(cliente.get(rota)).get("set-cookie") is None

    def test_sem_secret_key_a_sessao_nao_funciona(self, recarregar):
        app = recarregar(SECRET_KEY="")

        @app.route("/_sessao")
        def sessao():
            session["x"] = 1
            return "ok"

        assert app.test_client().get("/_sessao").status_code == 500

    def test_cookie_de_sessao_em_producao_e_httponly_secure_samesite_e_host_prefix(self, recarregar):
        app = recarregar(**PRODUCAO, SECRET_KEY=CHAVE_FORTE)

        @app.route("/_sessao")
        def sessao():
            session["x"] = 1
            return "ok"

        cookie = app.test_client().get("/_sessao", base_url="https://astra.example").headers["Set-Cookie"]
        assert cookie.startswith("__Host-astra=") and "HttpOnly" in cookie and "Secure" in cookie
        assert "SameSite=Lax" in cookie and "Path=/" in cookie and "Domain" not in cookie

    def test_cookie_em_desenvolvimento_continua_httponly_e_samesite(self, recarregar):
        app = recarregar(SECRET_KEY=CHAVE_FORTE)

        @app.route("/_sessao")
        def sessao():
            session["x"] = 1
            return "ok"

        cookie = app.test_client().get("/_sessao").headers["Set-Cookie"]
        assert "HttpOnly" in cookie and "SameSite=Lax" in cookie and "Secure" not in cookie

    @pytest.mark.parametrize("fraca", ["curta", "a" * 40, "changeme", "senha", "12345678" * 2])
    def test_secret_key_fraca_derruba_a_inicializacao_em_producao(self, fraca):
        with pytest.raises(ValueError, match="SECRET_KEY fraca"):
            config.validar_secret_key(fraca, producao=True)

    def test_secret_key_forte_e_ausente_sao_aceitas(self):
        assert config.validar_secret_key(CHAVE_FORTE, producao=True) == CHAVE_FORTE
        assert config.validar_secret_key("", producao=True) is None

    def test_secret_key_fraca_em_desenvolvimento_so_avisa(self, caplog):
        assert config.validar_secret_key("curta", producao=False) == "curta"
        assert "SECRET_KEY fraca" in caplog.text


class TestErrosNaoVazamDetalhes:
    def test_excecao_nao_tratada_vira_500_generico_sem_traceback(self, recarregar, caplog):
        app = recarregar()

        @app.route("/_explode")
        def explode():
            raise RuntimeError("segredo-interno /home/astra/servidor/main.py linha 42")

        resposta = app.test_client().get("/_explode")
        texto = resposta.get_data(as_text=True)
        assert resposta.status_code == 500 and resposta.get_json()["erro"] == "Ops, algo deu errado no servidor."
        assert "segredo-interno" not in texto and "Traceback" not in texto and ".py" not in texto
        assert "segredo-interno" not in caplog.text

    @pytest.mark.parametrize("metodo, rota, status", [("get", "/chat", 404), ("get", "/nada", 404),
                                                      ("post", "/health", 405), ("put", "/chat", 405)])
    def test_erros_http_sao_json_sem_pagina_do_framework(self, metodo, rota, status):
        main.limiter.reset()
        resposta = getattr(main.app.test_client(), metodo)(rota)
        assert resposta.status_code == status and resposta.is_json
        assert "Werkzeug" not in resposta.get_data(as_text=True)


class TestUsoDeInnerHtml:
    def trechos(self, arquivo):
        codigo = (RAIZ / "landing-page" / "js" / arquivo).read_text(encoding="utf-8")
        return re.findall(r"\.innerHTML\s*=\s*([^;]*);", codigo, flags=re.DOTALL)

    def test_quantidade_de_pontos_que_escrevem_html_nao_cresce_sem_revisao(self):
        assert len(self.trechos("script.js")) == 9
        assert len(self.trechos("home.js")) == 2

    def test_texto_do_modelo_so_entra_no_html_pelo_sanitizador(self):
        codigo = (RAIZ / "landing-page" / "js" / "script.js").read_text(encoding="utf-8")
        assert "renderMarkdown(text)" in codigo
        assert re.search(r"DOMPurify\.sanitize\(html, CONFIG_SANITIZACAO\)", codigo)
        assert "marked.parse(" in codigo and codigo.count("marked.parse(") == 1

    def test_nenhum_html_do_site_tem_script_ou_estilo_inline(self):
        for arquivo in ("index.html", "home.html"):
            html = (RAIZ / "landing-page" / arquivo).read_text(encoding="utf-8")
            assert not re.search(r"<script(?![^>]*\bsrc=)", html) and "<style" not in html
            assert not re.search(r"\sstyle=|\son[a-z]+=", html)
