from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import numpy as np

from rag.configuracao import MODELO_CACHE_DIR, MODELO_EMBEDDING

if TYPE_CHECKING:
    from fastembed import TextEmbedding

class Embedder(Protocol):
    nome: str

    def embed(self, textos: list[str]) -> np.ndarray:
        """Devolve uma matriz float32 (n, dimensão) com vetores de norma 1."""
        ...

def normalizar_linhas(matriz: np.ndarray) -> np.ndarray:
    """Norma 1 em cada linha: assim o produto interno do FAISS equivale ao cosseno."""
    normas = np.linalg.norm(matriz, axis=1, keepdims=True)
    normas[normas == 0] = 1.0
    return (matriz / normas).astype(np.float32)

class FastEmbedEmbedder:
    """Embeddings locais via ONNX (fastembed): sem chave de API e sem custo por chamada."""

    def __init__(self, nome: str = MODELO_EMBEDDING, pasta_cache: Path = MODELO_CACHE_DIR):
        self.nome = nome
        self._pasta_cache = pasta_cache
        self._modelo: TextEmbedding | None = None

    def embed(self, textos: list[str]) -> np.ndarray:
        if self._modelo is None:
            from fastembed import TextEmbedding
            self._modelo = TextEmbedding(self.nome, cache_dir=str(self._pasta_cache))
        matriz = np.array(list(self._modelo.embed(textos)), dtype=np.float32)
        return normalizar_linhas(matriz)
