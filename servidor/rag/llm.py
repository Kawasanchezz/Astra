from config import GROQ_API_KEY, GROQ_MAX_RETRIES, GROQ_MODEL, GROQ_TIMEOUT, MAX_TOKENS_RESPOSTA

_cliente = None

class LlmNaoConfigurado(RuntimeError):
    pass

def llm_groq(mensagens: list[dict]) -> str:
    """Chama a Groq com o mesmo modelo e limites do chat. Exige GROQ_API_KEY."""
    global _cliente
    if not GROQ_API_KEY:
        raise LlmNaoConfigurado("Defina GROQ_API_KEY em servidor/.env para usar o LLM.")
    if _cliente is None:
        from groq import Groq
        _cliente = Groq(api_key=GROQ_API_KEY, max_retries=GROQ_MAX_RETRIES)
    resposta = _cliente.chat.completions.create(
        model=GROQ_MODEL, messages=mensagens, temperature=0.2,
        max_tokens=MAX_TOKENS_RESPOSTA, timeout=GROQ_TIMEOUT,
    )
    return (resposta.choices[0].message.content or "").strip()
