from types import SimpleNamespace

from core.orcamento import SEGUNDOS_POR_DIA, OrcamentoDiario


def test_reserva_ate_o_limite_e_recusa_o_excedente():
    orcamento = OrcamentoDiario(100, relogio=lambda: 0.0)
    assert orcamento.reservar(60) and orcamento.reservar(40)
    assert not orcamento.reservar(1)
    assert orcamento.usado == 100


def test_gasto_real_menor_que_a_reserva_libera_o_excedente():
    orcamento = OrcamentoDiario(100, relogio=lambda: 0.0)
    orcamento.reservar(80)
    orcamento.acertar(80, 30)
    assert orcamento.usado == 30


def test_novo_dia_zera_o_consumo():
    agora = [0.0]
    orcamento = OrcamentoDiario(100, relogio=lambda: agora[0])
    assert orcamento.reservar(100)
    agora[0] = SEGUNDOS_POR_DIA + 1
    assert orcamento.reservar(100)


def test_chat_com_orcamento_esgotado_responde_429_sem_chamar_o_modelo(monkeypatch, groq, http):
    import services.ia_service as ia

    monkeypatch.setattr(ia, "orcamento_diario", OrcamentoDiario(1, relogio=lambda: 0.0))
    resposta = http.post("/chat", json={"mensagem": "oi"})
    assert resposta.status_code == 429
    assert int(resposta.headers["Retry-After"]) > 0
    assert groq.chamadas == []


def test_chat_registra_o_gasto_real_informado_pela_groq(monkeypatch, groq, http):
    import services.ia_service as ia

    def create(**kwargs):
        mensagem = SimpleNamespace(content="ok")
        return SimpleNamespace(choices=[SimpleNamespace(message=mensagem)],
                               usage=SimpleNamespace(total_tokens=50))

    monkeypatch.setattr(groq, "create", create)
    orcamento = OrcamentoDiario(10**9, relogio=lambda: 0.0)
    monkeypatch.setattr(ia, "orcamento_diario", orcamento)
    assert http.post("/chat", json={"mensagem": "oi"}).status_code == 200
    assert orcamento.usado == 50
