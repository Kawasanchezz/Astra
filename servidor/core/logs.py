import logging
import re
import uuid

from flask import g, has_request_context

_ID_VALIDO = re.compile(r"[A-Za-z0-9._-]{8,64}")

_SEGREDOS = re.compile(
    r"gsk_[A-Za-z0-9]{6,}"
    r"|sk-[A-Za-z0-9_-]{16,}"
    r"|(?i:bearer)\s+[A-Za-z0-9._~+/=-]{8,}"
    r"|[\w.+-]+@[\w-]+(?:\.[\w-]+)+"
)
MASCARA = "[oculto]"


def mascarar(texto: str) -> str:
    return _SEGREDOS.sub(MASCARA, texto)


def novo_id(recebido: str = "") -> str:
    """Reaproveita o id do cliente só se for curto e inofensivo (evita injeção de linhas no log)."""
    return recebido if _ID_VALIDO.fullmatch(recebido) else uuid.uuid4().hex[:16]


def id_atual() -> str:
    return g.get("id", "-") if has_request_context() else "-"


class FiltroDeLog(logging.Filter):
    """Tira chave, token e e-mail da mensagem e carimba o id da requisição no registro."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, dict):
            record.msg = {k: mascarar(v) if isinstance(v, str) else v for k, v in record.msg.items()}
        else:
            record.msg = mascarar(record.getMessage())
            record.args = None
        record.id = id_atual()
        return True


def configurar_logs() -> None:
    """Formato com id de correlação e filtro de segredos em todos os handlers. Pode ser chamada várias vezes."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(id)s]: %(message)s")
    for handler in logging.getLogger().handlers:
        if not any(isinstance(f, FiltroDeLog) for f in handler.filters):
            handler.addFilter(FiltroDeLog())
        if handler.formatter is None or "%(id)s" not in (handler.formatter._fmt or ""):
            handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(id)s]: %(message)s"))
