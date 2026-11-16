def test_csp_limita_enquadramento_base_e_formularios(http):
    csp = http.get("/health").headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in csp
    assert "base-uri 'self'" in csp
    assert "form-action 'self'" in csp


def test_csp_continua_sem_inline_nem_eval(http):
    csp = http.get("/health").headers["Content-Security-Policy"]
    assert "unsafe-inline" not in csp and "unsafe-eval" not in csp
