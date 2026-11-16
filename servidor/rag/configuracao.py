import os
from pathlib import Path

from dotenv import load_dotenv

SERVIDOR_DIR = Path(__file__).resolve().parent.parent
RAIZ = SERVIDOR_DIR.parent

load_dotenv(SERVIDOR_DIR / ".env")

def _env_int(nome: str, padrao: int) -> int:
    try:
        return int(os.environ.get(nome, str(padrao)))
    except (TypeError, ValueError):
        return padrao

def _env_float(nome: str, padrao: float) -> float:
    try:
        return float(os.environ.get(nome, str(padrao)))
    except (TypeError, ValueError):
        return padrao

DOCS_DIR = Path(os.environ.get("RAG_DOCS_DIR", RAIZ / "docs" / "estudo"))
PERGUNTAS_AVALIACAO = Path(os.environ.get("RAG_PERGUNTAS_AVALIACAO", RAIZ / "avaliacao" / "perguntas.json"))
PROMPTS_DIR = Path(os.environ.get("RAG_PROMPTS_DIR", RAIZ / "prompts"))
INDEX_DIR = Path(os.environ.get("RAG_INDEX_DIR", RAIZ / ".cache" / "rag-index"))
MODELO_CACHE_DIR = Path(os.environ.get("RAG_MODELO_CACHE_DIR", RAIZ / ".cache" / "fastembed"))

MODELO_EMBEDDING = os.environ.get(
    "RAG_MODELO_EMBEDDING", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# Este modelo corta o texto em ~128 tokens (cerca de 450 caracteres em português),
# então trechos maiores perderiam o final no embedding.
TAMANHO_TRECHO = _env_int("RAG_TAMANHO_TRECHO", 450)
SOBREPOSICAO = _env_int("RAG_SOBREPOSICAO", 80)

TOP_K = _env_int("RAG_TOP_K", 4)
SCORE_MINIMO = _env_float("RAG_SCORE_MINIMO", 0.35)

API_HOST = os.environ.get("RAG_API_HOST", "127.0.0.1")
API_PORT = _env_int("RAG_API_PORT", 8000)
API_MAX_PERGUNTA = _env_int("RAG_API_MAX_PERGUNTA", 500)
API_MAX_CORPO = _env_int("RAG_API_MAX_CORPO", 4096)
API_TIMEOUT_LLM = _env_float("RAG_API_TIMEOUT_LLM", 25.0)
# Se definido, /ask exige "Authorization: Bearer <token>" (chamada entre serviços).
API_TOKEN = os.environ.get("RAG_API_TOKEN") or None
