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


ESCUTAR_CSP = (
    "window.__csp = [];"
    "document.addEventListener('securitypolicyviolation',"
    " e => window.__csp.push(e.violatedDirective + ' ' + e.blockedURI));"
)


def test_navegacao_normal_nao_gera_violacao_de_csp(servidor, pagina):
    pagina.add_init_script(ESCUTAR_CSP)
    erros_de_console = []
    pagina.on("console", lambda m: erros_de_console.append(m.text) if "Content Security Policy" in m.text else None)

    pagina.goto(servidor + "/")
    pagina.wait_for_timeout(3_000)
    pagina.goto(servidor + "/app")
    pagina.wait_for_selector("#promptInput")
    pagina.locator("#sidebarOpen").click()
    pagina.locator("#accountBtn").click()
    pagina.locator("#menuIdioma").click()
    pagina.wait_for_selector("#idiomaGrade .idioma-item")
    pagina.keyboard.press("Escape")
    pagina.wait_for_timeout(500)

    assert pagina.evaluate("() => window.__csp") == []
    assert erros_de_console == []


def test_csp_bloqueia_script_e_estilo_injetados_na_pagina(servidor, pagina):
    pagina.add_init_script(ESCUTAR_CSP)
    pagina.goto(servidor + "/app")
    pagina.wait_for_selector("#promptInput")

    pagina.evaluate(
        "() => { const s = document.createElement('script'); s.textContent = 'window.__injetado = 1';"
        " document.body.appendChild(s);"
        " const t = document.createElement('style'); t.textContent = 'body { display: none }';"
        " document.head.appendChild(t); }")
    pagina.wait_for_timeout(300)

    assert pagina.evaluate("() => window.__injetado") is None
    violacoes = pagina.evaluate("() => window.__csp")
    assert any(v.startswith("script-src") for v in violacoes) and any(v.startswith("style-src") for v in violacoes)
    assert pagina.locator("body").is_visible()
