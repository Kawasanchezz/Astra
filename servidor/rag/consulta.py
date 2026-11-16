from __future__ import annotations

import secrets
from dataclasses import dataclass
from collections.abc import Callable

from rag.chunking import Trecho
from rag.configuracao import SCORE_MINIMO, TOP_K
from rag.embeddings import Embedder
from rag.indice import IndiceVetorial
from rag.prompts import Prompts, prompts_padrao

SEM_CONTEXTO = "Não encontrei isso nos documentos indexados, então prefiro não responder."

Llm = Callable[[list[dict]], str]

@dataclass(frozen=True)
class Resposta:
    texto: str
    trechos: list[tuple[Trecho, float]]
    usou_llm: bool
    versao_prompt: str = ""

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

def montar_mensagens(pergunta: str, encontrados: list[tuple[Trecho, float]],
                     prompts: Prompts | None = None) -> list[dict]:
    prompts = prompts or prompts_padrao()
    marca = secrets.token_hex(6)
    blocos = []
    for numero, (trecho, _) in enumerate(encontrados, start=1):
        origem = f"{trecho.fonte} > {trecho.secao}" if trecho.secao else trecho.fonte
        origem = origem.replace('"', "'").replace("\n", " ")
        blocos.append(f'<trecho-{marca} n="{numero}" fonte="{origem}">\n{trecho.texto}\n</trecho-{marca}>')
    return [
        {"role": "system", "content": prompts.mensagem_sistema},
        {"role": "user", "content": prompts.mensagem_usuario("\n\n".join(blocos), pergunta, marca)},
    ]

def perguntar(pergunta: str, indice: IndiceVetorial, embedder: Embedder, llm: Llm,
              k: int = TOP_K, score_minimo: float = SCORE_MINIMO,
              prompts: Prompts | None = None) -> Resposta:
    """Recupera o contexto e chama o LLM. Sem contexto relevante, nem chama o LLM."""
    prompts = prompts or prompts_padrao()
    encontrados = buscar_contexto(indice, embedder, pergunta, k, score_minimo)
    if not encontrados:
        return Resposta(SEM_CONTEXTO, [], usou_llm=False, versao_prompt=prompts.versao)
    texto = llm(montar_mensagens(pergunta, encontrados, prompts))
    return Resposta(texto, encontrados, usou_llm=True, versao_prompt=prompts.versao)
