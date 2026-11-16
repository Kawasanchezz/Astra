import os
import logging
from urllib.parse import urlsplit
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

logger = logging.getLogger(__name__)

def _env_int(nome: str, padrao: int) -> int:
    """Le um inteiro do ambiente sem quebrar se o valor vier invalido."""
    try:
        return int(os.environ.get(nome, str(padrao)))
    except (TypeError, ValueError):
        logger.warning("Valor invalido para %s no .env; usando padrao %s", nome, padrao)
        return padrao

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
CHAVE_PLACEHOLDER = "gsk_COLOQUE_SUA_CHAVE_AQUI"

def chave_groq_configurada() -> bool:
    return bool(GROQ_API_KEY) and GROQ_API_KEY != CHAVE_PLACEHOLDER

def restringir_logs_de_terceiros() -> None:
    for nome in ("groq", "httpx", "httpcore"):
        logging.getLogger(nome).setLevel(logging.WARNING)
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

_MODELOS_PADRAO = "openai/gpt-oss-120b,openai/gpt-oss-20b"
_modelos = {m.strip() for m in os.environ.get("ALLOWED_MODELS", _MODELOS_PADRAO).split(",") if m.strip()}
_modelos.add(GROQ_MODEL)
ALLOWED_MODELS = frozenset(_modelos)

NA_VERCEL = bool(os.environ.get("VERCEL"))
_PADRAO_ENV = "production" if NA_VERCEL else "development"
APP_ENV = os.environ.get("APP_ENV", _PADRAO_ENV).strip().lower()
IS_PRODUCTION = APP_ENV == "production"

PORT = _env_int("PORT", 5000)

TRUSTED_PROXY_COUNT = _env_int("TRUSTED_PROXY_COUNT", 1 if NA_VERCEL else 0)

FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
if IS_PRODUCTION and FLASK_DEBUG:
    logger.warning("FLASK_DEBUG=true ignorado em producao (seguranca): debugger desativado.")
    FLASK_DEBUG = False

def _origens_padrao() -> str:
    """Padrao do CORS: o dominio publico da Vercel (nunca localhost la)."""
    if NA_VERCEL:
        hosts = {os.environ.get("VERCEL_PROJECT_PRODUCTION_URL", ""), os.environ.get("VERCEL_URL", "")}
        urls = sorted(f"https://{h}" for h in hosts if h)
        if urls:
            return ",".join(urls)
    return "http://localhost:5000"

def normalizar_origens(brutas: list[str]) -> list[str]:
    validas: list[str] = []
    for bruta in brutas:
        origem = bruta.strip().rstrip("/")
        partes = urlsplit(origem)
        invalida = (origem in ("*", "null") or partes.scheme not in ("http", "https") or not partes.netloc
                    or bool(partes.path or partes.query or partes.fragment or partes.username))
        if invalida:
            logger.error("ALLOWED_ORIGINS: entrada invalida descartada (%.40r). Use origens exatas, "
                         "como https://seu-dominio.com.", bruta)
        elif origem not in validas:
            validas.append(origem)
    return validas

ALLOWED_ORIGINS = normalizar_origens(os.environ.get("ALLOWED_ORIGINS", _origens_padrao()).split(","))

CHAVES_SECRETAS_FRACAS = frozenset({"changeme", "secret", "senha", "password", "dev", "test", "troque", "coloque",
                                    "example", "exemplo"})

def validar_secret_key(valor: str, producao: bool) -> str | None:
    if not valor:
        return None
    fraca = len(valor) < 32 or len(set(valor)) < 8 or valor.lower() in CHAVES_SECRETAS_FRACAS
    if fraca and producao:
        raise ValueError("SECRET_KEY fraca: use 32 ou mais caracteres aleatorios, por exemplo "
                         "python -c 'import secrets; print(secrets.token_hex(32))'")
    if fraca:
        logger.warning("SECRET_KEY fraca: aceitavel so em desenvolvimento.")
    return valor

SECRET_KEY = validar_secret_key(os.environ.get("SECRET_KEY", ""), IS_PRODUCTION)

RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

FORCE_HTTPS = os.environ.get("FORCE_HTTPS", "true" if NA_VERCEL else "false").lower() == "true"

MAX_INPUT_LENGTH = 8000
MAX_HISTORY_SIZE = 16

MAX_HISTORY_CHARS = 12000

BYTES_POR_CARACTERE = 4
MAX_REQUEST_SIZE = BYTES_POR_CARACTERE * (MAX_INPUT_LENGTH + MAX_HISTORY_CHARS) + 16 * 1024

def calcular_timeout_llm(timeout_bruto: int, tentativas_extras: int, prazo_total: int) -> int:
    return max(5, min(timeout_bruto, prazo_total // (tentativas_extras + 1)))

GROQ_MAX_RETRIES = max(0, min(_env_int("GROQ_MAX_RETRIES", 1), 3))
PRAZO_TOTAL_LLM = _env_int("PRAZO_TOTAL_LLM", 25)
GROQ_TIMEOUT = calcular_timeout_llm(_env_int("GROQ_TIMEOUT", 30), GROQ_MAX_RETRIES, PRAZO_TOTAL_LLM)

CHAT_ENABLED = os.environ.get("CHAT_ENABLED", "true").strip().lower() != "false"
RATE_LIMIT_DEFAULT = "60 per minute"
RATE_LIMIT_CHAT = os.environ.get("RATE_LIMIT_CHAT", "20 per minute")
RATE_LIMIT_DIARIO = os.environ.get("RATE_LIMIT_DIARIO", "150 per day")

MAX_TOKENS_RESPOSTA = max(64, min(_env_int("MAX_TOKENS_RESPOSTA", 1024), 4096))

MAX_CONCURRENT_REQUESTS = _env_int("MAX_CONCURRENT_REQUESTS", 4)

RATE_LIMIT_GLOBAL = os.environ.get("RATE_LIMIT_GLOBAL", "300 per hour")
ORCAMENTO_DIARIO_TOKENS = _env_int("ORCAMENTO_DIARIO_TOKENS", 1000000)

def validar_configuracao():
    """Valida a configuracao e avisa sobre riscos de seguranca no boot."""
    if not chave_groq_configurada():
        logger.warning("⚠️ AVISO: Chave da Groq nao encontrada. O bot vai rodar em modo de teste.")

    if FORCE_HTTPS and TRUSTED_PROXY_COUNT == 0:
        logger.warning("FORCE_HTTPS=true com TRUSTED_PROXY_COUNT=0: se houver um proxy TLS "
                       "na frente, o redirect HTTP->HTTPS entra em loop infinito. "
                       "Defina TRUSTED_PROXY_COUNT=1 (ou o numero real de proxies).")

    if IS_PRODUCTION:
        if any(("localhost" in o or "127.0.0.1" in o) for o in ALLOWED_ORIGINS):
            logger.warning("ALLOWED_ORIGINS ainda aponta para localhost em producao. "
                           "Configure o dominio real (ex.: https://seu-dominio.com).")
        if not FORCE_HTTPS:
            logger.warning("FORCE_HTTPS=false em producao. Habilite HTTPS/HSTS atras do proxy TLS.")
        if RATELIMIT_STORAGE_URI.startswith("memory://"):
            logger.warning("RATELIMIT_STORAGE_URI=memory:// em producao: o limite nao e "
                           "compartilhado entre workers. Use redis:// para rate limit real.")
        if TRUSTED_PROXY_COUNT == 0:
            logger.warning("TRUSTED_PROXY_COUNT=0 em producao: se o app estiver atras de um "
                           "proxy (nginx/Cloudflare), o rate limit vai contar TODOS os clientes "
                           "como o mesmo IP (o do proxy). Defina o numero real de proxies.")

IDIOMAS = {
    "pt-BR": "Brazilian Portuguese", "pt-PT": "European Portuguese",
    "en-US": "English", "en-GB": "British English",
    "es-419": "Latin American Spanish", "es-ES": "Spanish (Spain)",
    "fr-FR": "French", "de-DE": "German", "it-IT": "Italian", "nl-NL": "Dutch",
    "da-DK": "Danish", "sv-SE": "Swedish", "nb-NO": "Norwegian", "fi-FI": "Finnish",
    "pl-PL": "Polish", "cs-CZ": "Czech", "ro-RO": "Romanian", "hu-HU": "Hungarian",
    "el-GR": "Greek", "ru-RU": "Russian", "uk-UA": "Ukrainian", "tr-TR": "Turkish",
    "ar": "Arabic", "he-IL": "Hebrew", "fa-IR": "Persian", "ur-PK": "Urdu",
    "hi-IN": "Hindi", "bn-BD": "Bangla", "bho-IN": "Bhojpuri", "gu-IN": "Gujarati",
    "mr-IN": "Marathi", "pa-IN": "Punjabi", "ta-IN": "Tamil", "te-IN": "Telugu",
    "kn-IN": "Kannada", "ml-IN": "Malayalam", "ne-NP": "Nepali",
    "zh-CN": "Simplified Chinese", "zh-TW": "Traditional Chinese", "ja-JP": "Japanese",
    "ko-KR": "Korean", "id-ID": "Indonesian", "ms-MY": "Malay", "fil-PH": "Filipino",
    "th-TH": "Thai", "vi-VN": "Vietnamese", "sw": "Swahili", "am-ET": "Amharic",
    "ha": "Hausa", "yo": "Yoruba", "zu": "Zulu",
}
