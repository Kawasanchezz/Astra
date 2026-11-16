import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "servidor"))
os.environ["GROQ_API_KEY"] = ""
os.environ["APP_ENV"] = "development"

RESPOSTA_FALSA = "resposta de teste"


class ClienteGroqFalso:
    """Substitui o cliente da Groq: guarda o que recebeu e nunca usa a rede."""

    def __init__(self):
        self.chamadas = []

    def create(self, **kwargs):
        self.chamadas.append(kwargs)
        mensagem = SimpleNamespace(content=RESPOSTA_FALSA)
        return SimpleNamespace(choices=[SimpleNamespace(message=mensagem)], usage=None)


@pytest.fixture
def groq(monkeypatch):
    import services.ia_service as ia

    cliente = ClienteGroqFalso()
    monkeypatch.setattr(ia, "client", SimpleNamespace(chat=SimpleNamespace(completions=cliente)))
    return cliente


@pytest.fixture
def http():
    import main

    main.limiter.reset()
    return main.app.test_client()
