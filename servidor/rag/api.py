from __future__ import annotations

import hmac
import logging
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as PrazoEsgotado
from dataclasses import dataclass

from flask import Flask, Response, g, jsonify, request
from werkzeug.exceptions import HTTPException

from rag.configuracao import SCORE_MINIMO, TOP_K
from rag.consulta import Llm, perguntar
from rag.embeddings import Embedder
from rag.indice import IndiceVetorial
from rag.llm import LlmNaoConfigurado
from rag.prompts import Prompts, prompts_padrao

logger = logging.getLogger("rag.api")

_ID_VALIDO = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_CODIGOS_HTTP = {404: "nao_encontrado", 405: "metodo_nao_permitido", 413: "corpo_grande"}

@dataclass(frozen=True)
class Limites:
    max_pergunta: int = 500
    max_corpo: int = 4096
    timeout_llm: float = 25.0
    max_k: int = 10

class ErroApi(Exception):
    def __init__(self, status: int, codigo: str, mensagem: str):
        super().__init__(mensagem)
        self.status, self.codigo, self.mensagem = status, codigo, mensagem

def _erro(status: int, codigo: str, mensagem: str):
    return jsonify({"erro": {"codigo": codigo, "mensagem": mensagem}, "id": g.get("id")}), status

def criar_app(indice: IndiceVetorial | None, embedder: Embedder, llm: Llm, prompts: Prompts | None = None,
              limites: Limites = Limites(), token: str | None = None,
              k_padrao: int = TOP_K, score_minimo: float = SCORE_MINIMO) -> Flask:
    """Monta a API. Tudo que muda entre produção e teste (índice, embedder, LLM) entra por parâmetro."""
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = limites.max_corpo
    prompts = prompts or prompts_padrao()
    executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="llm")

    def llm_com_prazo(mensagens: list[dict]) -> str:
        """Chama o LLM com prazo. Qualquer falha vira um erro HTTP genérico, sem vazar detalhe interno."""
        futuro = executor.submit(llm, mensagens)
        try:
            return futuro.result(timeout=limites.timeout_llm)
        except PrazoEsgotado:
            futuro.cancel()
            raise ErroApi(504, "llm_timeout", "O modelo demorou demais para responder.")
        except LlmNaoConfigurado:
            raise ErroApi(503, "llm_nao_configurado", "O modelo não está configurado neste serviço.")
        except Exception as e:
            g.log["erro_tipo"] = type(e).__name__
            raise ErroApi(502, "llm_erro", "O modelo não respondeu. Tente novamente em instantes.")

    @app.before_request
    def iniciar():
        g.inicio = time.perf_counter()
        g.log = {}
        recebido = request.headers.get("X-Request-ID", "")
        g.id = recebido if _ID_VALIDO.match(recebido) else uuid.uuid4().hex[:16]
        if request.content_length and request.content_length > limites.max_corpo:
            raise ErroApi(413, "corpo_grande", f"O corpo passa de {limites.max_corpo} bytes.")
        if token and request.path == "/ask":
            enviado = request.headers.get("Authorization", "")
            if not hmac.compare_digest(enviado.encode(), f"Bearer {token}".encode()):
                raise ErroApi(401, "nao_autorizado", "Token ausente ou inválido.")

    @app.after_request
    def finalizar(resposta: Response) -> Response:
        resposta.headers["X-Request-ID"] = g.get("id", "")
        logger.info({
            "evento": "requisicao", "id": g.get("id"), "metodo": request.method, "rota": request.path,
            "status": resposta.status_code,
            "duracao_ms": round((time.perf_counter() - g.get("inicio", time.perf_counter())) * 1000, 1),
            **g.get("log", {}),
        })
        return resposta

    @app.get("/health")
    def health():
        pronto = indice is not None
        corpo = {"status": "ok" if pronto else "indice_indisponivel", "versao_prompt": prompts.versao,
                 "trechos_indexados": len(indice.trechos) if pronto else 0,
                 "modelo_embedding": embedder.nome}
        return jsonify(corpo), 200 if pronto else 503

    @app.post("/ask")
    def ask():
        if not request.is_json:
            raise ErroApi(415, "tipo_invalido", "Envie JSON com Content-Type: application/json.")
        dados = request.get_json(silent=True)
        if not isinstance(dados, dict):
            raise ErroApi(400, "json_invalido", "O corpo precisa ser um objeto JSON.")
        pergunta = dados.get("pergunta")
        if not isinstance(pergunta, str):
            raise ErroApi(400, "pergunta_invalida", "O campo 'pergunta' é obrigatório e deve ser texto.")
        pergunta = pergunta.strip()
        if not pergunta:
            raise ErroApi(400, "pergunta_vazia", "A pergunta está vazia.")
        if len(pergunta) > limites.max_pergunta:
            raise ErroApi(400, "pergunta_longa", f"A pergunta passa de {limites.max_pergunta} caracteres.")
        k = dados.get("k", k_padrao)
        if isinstance(k, bool) or not isinstance(k, int) or not 1 <= k <= limites.max_k:
            raise ErroApi(400, "k_invalido", f"'k' deve ser um inteiro entre 1 e {limites.max_k}.")
        if indice is None:
            raise ErroApi(503, "indice_indisponivel", "O índice de documentos não foi carregado.")

        g.log.update(pergunta_chars=len(pergunta), k=k)
        resposta = perguntar(pergunta, indice, embedder, llm_com_prazo, k, score_minimo, prompts)
        g.log.update(usou_llm=resposta.usou_llm, trechos=len(resposta.trechos))
        return jsonify({
            "id": g.id,
            "resposta": resposta.texto,
            "usou_llm": resposta.usou_llm,
            "fontes": [{"arquivo": t.fonte, "secao": t.secao, "score": round(s, 3)} for t, s in resposta.trechos],
            "versao_prompt": resposta.versao_prompt,
        })

    @app.errorhandler(ErroApi)
    def erro_da_api(e: ErroApi):
        g.log.setdefault("erro_codigo", e.codigo)
        return _erro(e.status, e.codigo, e.mensagem)

    @app.errorhandler(HTTPException)
    def erro_http(e: HTTPException):
        codigo = _CODIGOS_HTTP.get(e.code, "requisicao_invalida")
        g.setdefault("log", {})["erro_codigo"] = codigo
        return _erro(e.code or 400, codigo, "Requisição inválida." if (e.code or 400) < 500 else "Erro no servidor.")

    @app.errorhandler(Exception)
    def erro_inesperado(e: Exception):
        g.setdefault("log", {}).update(erro_codigo="erro_interno", erro_tipo=type(e).__name__)
        return _erro(500, "erro_interno", "Erro interno no servidor.")

    return app
