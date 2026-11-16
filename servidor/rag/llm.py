import threading
from typing import cast

from groq.types.chat import ChatCompletionMessageParam

from core.orcamento import estimar_tokens, orcamento_diario
from config import (GROQ_API_KEY, GROQ_MAX_RETRIES, GROQ_MODEL, GROQ_TIMEOUT, MAX_TOKENS_RESPOSTA,
                    chave_groq_configurada, restringir_logs_de_terceiros)

restringir_logs_de_terceiros()

_cliente = None
_trava_cliente = threading.Lock()

class LlmNaoConfigurado(RuntimeError):
    pass

class OrcamentoEsgotado(RuntimeError):
    pass

def _obter_cliente():
    global _cliente
    with _trava_cliente:
        if _cliente is None:
            from groq import Groq
            _cliente = Groq(api_key=GROQ_API_KEY, max_retries=GROQ_MAX_RETRIES)
        return _cliente

def llm_groq(mensagens: list[dict]) -> str:
    """Chama a Groq com o mesmo modelo e limites do chat. Exige GROQ_API_KEY."""
    if not chave_groq_configurada():
        raise LlmNaoConfigurado("Defina GROQ_API_KEY em servidor/.env para usar o LLM.")
    estimativa = sum(estimar_tokens(str(m.get("content") or "")) for m in mensagens) + MAX_TOKENS_RESPOSTA
    if not orcamento_diario.reservar(estimativa):
        raise OrcamentoEsgotado("orcamento diario de tokens esgotado")
    try:
        resposta = _obter_cliente().chat.completions.create(
            model=GROQ_MODEL, messages=cast(list[ChatCompletionMessageParam], mensagens), temperature=0.2,
            max_tokens=MAX_TOKENS_RESPOSTA, timeout=GROQ_TIMEOUT,
        )
    except Exception:
        orcamento_diario.acertar(estimativa, 0)
        raise
    gasto_real = getattr(getattr(resposta, "usage", None), "total_tokens", None)
    orcamento_diario.acertar(estimativa, gasto_real if isinstance(gasto_real, int) else None)
    return (resposta.choices[0].message.content or "").strip()
