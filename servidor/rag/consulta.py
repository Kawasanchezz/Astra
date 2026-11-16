from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from rag.chunking import Trecho
from rag.configuracao import SCORE_MINIMO, TOP_K
from rag.embeddings import Embedder
from rag.indice import IndiceVetorial

REGRA_SISTEMA = (
    "Você responde perguntas usando SOMENTE o contexto fornecido. "
    "Se o contexto não tiver a resposta, diga que não sabe; não use conhecimento externo. "
    "Responda em português, de forma curta e direta, e cite as fontes no formato [1], [2]."
)
SEM_CONTEXTO = "Não encontrei isso nos documentos indexados, então prefiro não responder."

Llm = Callable[[list[dict]], str]

@dataclass(frozen=True)
class Resposta:
    texto: str
    trechos: list[tuple[Trecho, float]]
    usou_llm: bool

    @property
    def fontes(self) -> list[str]:
        vistas: list[str] = []
        for trecho, _ in self.trechos:
            if trecho.fonte not in vistas:
                vistas.append(trecho.fonte)
        return vistas

def buscar_contexto(indice: IndiceVetorial, embedder: Embedder, pergunta: str,
                    k: int = TOP_K, score_minimo: float = SCORE_MINIMO) -> list[tuple[Trecho, float]]:
    """Trechos mais parecidos com a pergunta, descartando os abaixo do score mínimo."""
    vetor = embedder.embed([pergunta])[0]
    return [(t, s) for t, s in indice.buscar(vetor, k) if s >= score_minimo]

def montar_mensagens(pergunta: str, encontrados: list[tuple[Trecho, float]]) -> list[dict]:
    blocos = []
    for numero, (trecho, _) in enumerate(encontrados, start=1):
        origem = f"{trecho.fonte} > {trecho.secao}" if trecho.secao else trecho.fonte
        blocos.append(f"[{numero}] (fonte: {origem})\n{trecho.texto}")
    contexto = "\n\n".join(blocos)
    return [
        {"role": "system", "content": REGRA_SISTEMA},
        {"role": "user", "content": f"Contexto:\n{contexto}\n\nPergunta: {pergunta}"},
    ]

def perguntar(pergunta: str, indice: IndiceVetorial, embedder: Embedder, llm: Llm,
              k: int = TOP_K, score_minimo: float = SCORE_MINIMO) -> Resposta:
    """Recupera o contexto e chama o LLM. Sem contexto relevante, nem chama o LLM."""
    encontrados = buscar_contexto(indice, embedder, pergunta, k, score_minimo)
    if not encontrados:
        return Resposta(SEM_CONTEXTO, [], usou_llm=False)
    return Resposta(llm(montar_mensagens(pergunta, encontrados)), encontrados, usou_llm=True)
