from conftest import RESPOSTA_FALSA


def test_mensagem_normal_chama_o_modelo_uma_vez(groq, http):
    resposta = http.post("/chat", json={"mensagem": "Explique listas em Python"})
    assert resposta.status_code == 200
    assert resposta.get_json() == {"resposta": RESPOSTA_FALSA}
    assert len(groq.chamadas) == 1


def test_mensagem_vazia_nao_chama_o_modelo(groq, http):
    resposta = http.post("/chat", json={"mensagem": "   "})
    assert resposta.status_code == 400
    assert groq.chamadas == []
