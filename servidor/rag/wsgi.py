"""Entrada de produção: gunicorn --workers 1 --threads 4 rag.wsgi:app (dentro de servidor/)."""
import logging

from rag.api import Limites, criar_app
from rag.configuracao import (API_LIMITE, API_MAX_CORPO, API_MAX_PERGUNTA, API_TIMEOUT_LLM, API_TOKEN,
                              INDEX_DIR, MODELO_EMBEDDING)
from rag.embeddings import FastEmbedEmbedder
from rag.indice import IndiceVetorial
from rag.llm import llm_groq
from rag.logs import configurar_logs

def criar_app_padrao():
    configurar_logs()
    logger = logging.getLogger("rag.api")
    embedder = FastEmbedEmbedder()
    try:
        indice = IndiceVetorial.carregar(INDEX_DIR, modelo_esperado=MODELO_EMBEDDING)
        embedder.embed(["aquecimento"])
    except FileNotFoundError:
        indice = None
        logger.error({"evento": "indice_ausente", "pasta": str(INDEX_DIR),
                      "acao": "rode: python -m rag indexar"})
    return criar_app(indice, embedder, llm_groq,
                     limites=Limites(max_pergunta=API_MAX_PERGUNTA, max_corpo=API_MAX_CORPO,
                                     timeout_llm=API_TIMEOUT_LLM, limite_de_requisicoes=API_LIMITE),
                     token=API_TOKEN)

app = criar_app_padrao()
