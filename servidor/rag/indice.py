from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import faiss
import numpy as np

from rag.chunking import Trecho, dividir_markdown
from rag.configuracao import SOBREPOSICAO, TAMANHO_TRECHO
from rag.embeddings import Embedder

ARQ_FAISS = "indice.faiss"
ARQ_TRECHOS = "trechos.json"
ARQ_META = "meta.json"

class IndiceVetorial:
    """Índice FAISS exato (IndexFlatIP) mais a lista de trechos na mesma ordem dos vetores."""

    def __init__(self, indice: faiss.Index, trechos: list[Trecho], modelo: str):
        if indice.ntotal != len(trechos):
            raise ValueError("o índice e a lista de trechos têm tamanhos diferentes")
        self._indice = indice
        self.trechos = trechos
        self.modelo = modelo

    @classmethod
    def construir(cls, trechos: list[Trecho], embedder: Embedder) -> IndiceVetorial:
        if not trechos:
            raise ValueError("nenhum trecho para indexar")
        vetores = embedder.embed([t.texto_para_embedding for t in trechos])
        indice = faiss.IndexFlatIP(vetores.shape[1])
        indice.add(vetores)
        return cls(indice, list(trechos), embedder.nome)

    def buscar(self, vetor: np.ndarray, k: int) -> list[tuple[Trecho, float]]:
        """Os k trechos mais parecidos, do mais para o menos, com a similaridade de cosseno."""
        consulta = np.asarray(vetor, dtype=np.float32).reshape(1, -1)
        scores, posicoes = self._indice.search(consulta, min(k, len(self.trechos)))
        return [(self.trechos[p], float(s)) for s, p in zip(scores[0], posicoes[0], strict=True) if p != -1]

    def salvar(self, pasta: Path) -> None:
        pasta = Path(pasta)
        pasta.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._indice, str(pasta / ARQ_FAISS))
        (pasta / ARQ_TRECHOS).write_text(
            json.dumps([asdict(t) for t in self.trechos], ensure_ascii=False, indent=1), encoding="utf-8")
        (pasta / ARQ_META).write_text(
            json.dumps({"modelo": self.modelo, "trechos": len(self.trechos)}), encoding="utf-8")

    @classmethod
    def carregar(cls, pasta: Path, modelo_esperado: str | None = None) -> IndiceVetorial:
        pasta = Path(pasta)
        meta = json.loads((pasta / ARQ_META).read_text(encoding="utf-8"))
        if modelo_esperado and meta["modelo"] != modelo_esperado:
            raise ValueError(
                f"índice criado com {meta['modelo']} mas o modelo atual é {modelo_esperado}; reindexe")
        trechos = [Trecho(**t) for t in json.loads((pasta / ARQ_TRECHOS).read_text(encoding="utf-8"))]
        return cls(faiss.read_index(str(pasta / ARQ_FAISS)), trechos, meta["modelo"])

def indexar_pasta(pasta_docs: Path, embedder: Embedder,
                  tamanho: int = TAMANHO_TRECHO, sobreposicao: int = SOBREPOSICAO) -> IndiceVetorial:
    """Lê todos os .md da pasta (e subpastas), divide em trechos e constrói o índice."""
    pasta_docs = Path(pasta_docs)
    trechos: list[Trecho] = []
    for arquivo in sorted(pasta_docs.rglob("*.md")):
        fonte = arquivo.relative_to(pasta_docs).as_posix()
        trechos.extend(dividir_markdown(arquivo.read_text(encoding="utf-8"), fonte, tamanho, sobreposicao))
    return IndiceVetorial.construir(trechos, embedder)
