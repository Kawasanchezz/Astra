import json
import logging
import sys
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    """Uma linha JSON por registro. Se a mensagem já for um dict, os campos entram direto."""

    def format(self, record: logging.LogRecord) -> str:
        campos = record.msg if isinstance(record.msg, dict) else {"mensagem": record.getMessage()}
        linha = {"ts": datetime.fromtimestamp(record.created, timezone.utc).isoformat(timespec="milliseconds"),
                 "nivel": record.levelname, **campos}
        return json.dumps(linha, ensure_ascii=False)

def configurar_logs(nivel: int = logging.INFO) -> None:
    """Liga o log JSON do pacote rag. Pode ser chamada mais de uma vez."""
    logger = logging.getLogger("rag")
    if any(isinstance(h.formatter, JsonFormatter) for h in logger.handlers):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(nivel)
    logger.propagate = False
