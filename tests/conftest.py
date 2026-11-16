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
