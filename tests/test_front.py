import threading

import pytest

playwright_api = pytest.importorskip("playwright.sync_api")

import main  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402


@pytest.fixture(scope="module")
def servidor():
    main.limiter.reset()
    http = make_server("127.0.0.1", 0, main.app, threaded=True)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{http.server_port}"
    http.shutdown()


@pytest.fixture
def pagina():
    with playwright_api.sync_playwright() as p:
        try:
            navegador = p.chromium.launch(channel="chrome", headless=True)
        except playwright_api.Error:
            pytest.skip("Chrome não está disponível para o Playwright")
        contexto = navegador.new_context(viewport={"width": 1280, "height": 760})
        contexto.add_init_script("localStorage.setItem('astra_idioma','pt-BR');")
        yield contexto.new_page()
        navegador.close()


def test_requisicao_sem_resposta_nao_trava_a_interface_para_sempre(servidor, pagina):
    pagina.clock.install()
    pagina.route("**/chat", lambda rota: None)
    pagina.goto(servidor + "/app")
    pagina.clock.run_for(8_000)
    pagina.wait_for_selector("#promptInput")

    pagina.fill("#promptInput", "Explique listas em Python")
    pagina.click("#sendBtn")
    assert pagina.locator("#sendBtn").is_disabled()

    pagina.clock.run_for(120_000)
    playwright_api.expect(pagina.locator("#sendBtn")).to_be_enabled(timeout=5_000)
    assert pagina.locator("#messages").inner_text().strip() != ""
