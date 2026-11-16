import os
import sys
from pathlib import Path

os.environ["GROQ_API_KEY"] = "chave-falsa-de-teste"
os.environ["APP_ENV"] = "development"
os.environ["RATE_LIMIT_CHAT"] = "100000 per minute"
os.environ["RATE_LIMIT_DIARIO"] = "100000 per day"
os.environ["RATE_LIMIT_GLOBAL"] = "100000 per hour"
os.environ["ORCAMENTO_DIARIO_TOKENS"] = "0"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "servidor"))


import pytest  # noqa: E402


@pytest.fixture
def usar_llm(monkeypatch):
    import main
    from apoio import ClienteFalso
    from services import ia_service

    main.limiter.reset()

    def instalar(comportamento):
        cliente = ClienteFalso(comportamento)
        monkeypatch.setattr(ia_service, "client", cliente)
        return cliente

    def proibido(_):
        raise AssertionError("LLM real não pode ser chamado")

    monkeypatch.setattr(ia_service, "client", ClienteFalso(proibido))
    return instalar


@pytest.fixture(scope="session")
def servidor():
    import threading

    import main
    from werkzeug.serving import make_server

    http = make_server("127.0.0.1", 0, main.app, threaded=True)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{http.server_port}"
    http.shutdown()


@pytest.fixture
def pagina():
    import main

    api = pytest.importorskip("playwright.sync_api")
    main.limiter.reset()
    with api.sync_playwright() as p:
        navegador = None
        for opcoes in ({"channel": "chrome"}, {}):
            try:
                navegador = p.chromium.launch(headless=True, **opcoes)
                break
            except Exception:
                continue
        if navegador is None:
            if os.environ.get("CI"):
                pytest.fail("Nenhum navegador disponível no CI: os testes de XSS e CSP não podem ser pulados")
            pytest.skip("Nenhum navegador disponível para o Playwright (rode: playwright install chromium)")
        contexto = navegador.new_context(viewport={"width": 1280, "height": 760})
        contexto.add_init_script("localStorage.setItem('astra_idioma','pt-BR');")
        yield contexto.new_page()
        navegador.close()


@pytest.fixture
def recarregar(monkeypatch):
    import importlib

    import config
    import main

    def aplicar(**ambiente):
        if ambiente.get("APP_ENV") == "production":
            ambiente.setdefault("ORCAMENTO_DIARIO_TOKENS", "1000000")
        for nome, valor in ambiente.items():
            monkeypatch.setenv(nome, valor)
        importlib.reload(config)
        importlib.reload(main)
        return main.app

    yield aplicar
    monkeypatch.undo()
    importlib.reload(config)
    importlib.reload(main)
