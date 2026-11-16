import json
from types import SimpleNamespace

import httpx

import main

PEDIDO = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")


def resposta_llm(texto):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=texto))])


class ClienteFalso:
    def __init__(self, comportamento):
        self.chamadas = []

        def create(**kwargs):
            self.chamadas.append(kwargs)
            return comportamento(kwargs)

        self.chat = SimpleNamespace(completions=SimpleNamespace(create=create))


def erro_http(classe, status):
    resposta = httpx.Response(status, request=PEDIDO)
    return classe("erro do provedor com detalhe-interno-secreto", response=resposta, body=None)


def perguntar(corpo):
    try:
        enviado = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
    except UnicodeEncodeError:
        enviado = json.dumps(corpo).encode("ascii")
    return main.app.test_client().post("/chat", data=enviado, content_type="application/json")
