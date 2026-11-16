from __future__ import annotations

import json
import re
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from rag.consulta import Llm, perguntar
from rag.configuracao import SCORE_MINIMO, TOP_K
from rag.embeddings import Embedder
from rag.indice import IndiceVetorial
from rag.prompts import Prompts, prompts_padrao

_CITACAO = re.compile(r"\[(\d+)\]")
_CITACAO_LARGA = re.compile(r"【(\d+)】")
_FRASES_DE_RECUSA = ("nao sei com base nos documentos", "nao encontrei isso nos documentos")

@dataclass(frozen=True)
class Pergunta:
    id: str
    pergunta: str
    esperado: str
    fonte: str | None
    termos: list[list[str]]

    @property
    def deve_responder(self) -> bool:
        return self.fonte is not None

@dataclass
class Resultado:
    id: str
    pergunta: str
    esperado: str
    resposta: str
    recuperados: list[dict]
    deve_responder: bool
    recuperou_fonte: bool = False
    fonte_em_primeiro: bool = False
    recusou: bool = False
    citou_fonte_certa: bool = False
    citacao_invalida: bool = False
    formato_citacao_ok: bool = False
    termos_ok: bool = False
    aprovado: bool = False
    motivos_de_falha: list[str] = field(default_factory=list)

def carregar_perguntas(caminho: Path) -> list[Pergunta]:
    return [Pergunta(**item) for item in json.loads(Path(caminho).read_text(encoding="utf-8"))]

def _normalizar(texto: str) -> str:
    sem_acento = "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))
    return sem_acento.lower()

def eh_recusa(texto: str) -> bool:
    limpo = _normalizar(texto).strip()
    return limpo.startswith("nao sei") or any(frase in limpo for frase in _FRASES_DE_RECUSA)

def contem_termos(texto: str, termos: list[list[str]]) -> bool:
    """Todos os grupos precisam aparecer; dentro de um grupo basta uma das alternativas."""
    limpo = _normalizar(texto)
    return all(any(_normalizar(alt) in limpo for alt in grupo) for grupo in termos)

def avaliar_pergunta(item: Pergunta, indice: IndiceVetorial, embedder: Embedder, llm: Llm,
                     k: int, score_minimo: float, prompts: Prompts) -> Resultado:
    resposta = perguntar(item.pergunta, indice, embedder, llm, k, score_minimo, prompts)
    fontes_na_ordem = [t.fonte for t, _ in resposta.trechos]
    resultado = Resultado(
        id=item.id, pergunta=item.pergunta, esperado=item.esperado, resposta=resposta.texto,
        recuperados=[{"fonte": t.fonte, "secao": t.secao, "score": round(s, 3)} for t, s in resposta.trechos],
        deve_responder=item.deve_responder, recusou=eh_recusa(resposta.texto),
    )
    if not item.deve_responder:
        resultado.aprovado = resultado.recusou
        if not resultado.recusou:
            resultado.motivos_de_falha.append("respondeu algo que os documentos não cobrem")
        return resultado

    resultado.recuperou_fonte = item.fonte in fontes_na_ordem
    resultado.fonte_em_primeiro = bool(fontes_na_ordem) and fontes_na_ordem[0] == item.fonte
    numeros = [int(n) for n in _CITACAO.findall(resposta.texto)]
    resultado.formato_citacao_ok = bool(numeros) and not _CITACAO_LARGA.search(resposta.texto)
    numeros += [int(n) for n in _CITACAO_LARGA.findall(resposta.texto)]
    resultado.citacao_invalida = any(n < 1 or n > len(fontes_na_ordem) for n in numeros)
    resultado.citou_fonte_certa = any(
        1 <= n <= len(fontes_na_ordem) and fontes_na_ordem[n - 1] == item.fonte for n in numeros)
    resultado.termos_ok = contem_termos(resposta.texto, item.termos)

    if resultado.recusou:
        resultado.motivos_de_falha.append("recusou uma pergunta que os documentos cobrem")
    if not resultado.recuperou_fonte:
        resultado.motivos_de_falha.append("o documento certo não foi recuperado")
    if not resultado.citou_fonte_certa:
        resultado.motivos_de_falha.append("não citou o trecho do documento certo")
    if resultado.citacao_invalida:
        resultado.motivos_de_falha.append("citou um número de trecho que não existe")
    if not resultado.termos_ok:
        resultado.motivos_de_falha.append("faltam os termos esperados na resposta")
    resultado.aprovado = not resultado.motivos_de_falha
    return resultado

def avaliar(perguntas: list[Pergunta], indice: IndiceVetorial, embedder: Embedder, llm: Llm,
            k: int = TOP_K, score_minimo: float = SCORE_MINIMO, prompts: Prompts | None = None,
            pausa: float = 0.0) -> list[Resultado]:
    prompts = prompts or prompts_padrao()
    resultados = []
    for item in perguntas:
        resultados.append(avaliar_pergunta(item, indice, embedder, llm, k, score_minimo, prompts))
        if pausa:
            time.sleep(pausa)
    return resultados

def resumir(resultados: list[Resultado]) -> dict:
    com_resposta = [r for r in resultados if r.deve_responder]
    sem_resposta = [r for r in resultados if not r.deve_responder]
    return {
        "perguntas": len(resultados),
        "aprovadas": sum(r.aprovado for r in resultados),
        "responder": {
            "total": len(com_resposta),
            "recuperou_documento_certo": sum(r.recuperou_fonte for r in com_resposta),
            "documento_certo_em_primeiro": sum(r.fonte_em_primeiro for r in com_resposta),
            "citou_fonte_certa": sum(r.citou_fonte_certa for r in com_resposta),
            "citacao_no_formato": sum(r.formato_citacao_ok for r in com_resposta),
            "citacao_invalida": sum(r.citacao_invalida for r in com_resposta),
            "termos_esperados": sum(r.termos_ok for r in com_resposta),
            "recusou_indevidamente": sum(r.recusou for r in com_resposta),
        },
        "recusar": {
            "total": len(sem_resposta),
            "recusou_corretamente": sum(r.recusou for r in sem_resposta),
        },
    }
