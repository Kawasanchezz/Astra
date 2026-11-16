import pytest

playwright_api = pytest.importorskip("playwright.sync_api")


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
