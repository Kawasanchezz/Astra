import threading

import pytest
from werkzeug.serving import make_server

PAYLOAD_MALICIOSO = (
    "Texto <form action='https://evil.test'><input name='senha'></form> "
    "<img src='https://evil.test/x.png'> <style>body{display:none}</style> fim"
)


@pytest.fixture(scope="module")
def servidor_url():
    import main

    servidor = make_server("127.0.0.1", 0, main.app)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{servidor.server_port}"
    servidor.shutdown()


@pytest.fixture
def pagina():
    api = pytest.importorskip("playwright.sync_api")
    with api.sync_playwright() as p:
        navegador = p.chromium.launch(channel="chrome", headless=True)
        yield navegador.new_context().new_page()
        navegador.close()


def test_html_da_resposta_do_modelo_nao_cria_elementos_perigosos(servidor_url, pagina):
    pagina.route("**/chat", lambda rota: rota.fulfill(json={"resposta": PAYLOAD_MALICIOSO}))
    pagina.goto(servidor_url + "/app")
    pagina.wait_for_selector("#promptInput")
    pagina.fill("#promptInput", "oi")
    pagina.click("#sendBtn")
    pagina.wait_for_selector("#messages .msg--bot")
    proibidos = pagina.evaluate(
        "document.querySelectorAll('#messages form, #messages input, #messages img, #messages style').length"
    )
    assert proibidos == 0
