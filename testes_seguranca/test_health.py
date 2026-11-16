def test_health_em_producao_nao_revela_configuracao(monkeypatch, http):
    import main

    monkeypatch.setattr(main, "IS_PRODUCTION", True)
    resposta = http.get("/health")
    assert resposta.status_code == 200
    assert resposta.get_json() == {"status": "Online e Seguro!"}
