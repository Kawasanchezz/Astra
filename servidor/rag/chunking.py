from __future__ import annotations

import re
from dataclasses import dataclass

@dataclass(frozen=True)
class Trecho:
    fonte: str
    secao: str
    texto: str

    @property
    def texto_para_embedding(self) -> str:
        """O título da seção entra no embedding: dá contexto a trechos curtos."""
        return f"{self.secao}\n{self.texto}" if self.secao else self.texto

_TITULO = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_CERCA = re.compile(r"^\s*(```|~~~)")

def _secoes(markdown: str) -> list[tuple[str, list[str]]]:
    """Separa o Markdown por títulos. Devolve (caminho do título, linhas da seção)."""
    titulos: dict[int, str] = {}
    secoes: list[tuple[str, list[str]]] = [("", [])]
    em_cerca = False

    for linha in markdown.splitlines():
        if _CERCA.match(linha):
            em_cerca = not em_cerca
        achou = None if em_cerca else _TITULO.match(linha)
        if achou:
            nivel = len(achou.group(1))
            titulos = {n: t for n, t in titulos.items() if n < nivel}
            titulos[nivel] = achou.group(2)
            secoes.append((" > ".join(titulos[n] for n in sorted(titulos)), []))
        else:
            secoes[-1][1].append(linha)
    return secoes

def _blocos(linhas: list[str]) -> list[str]:
    """Parágrafos separados por linha em branco; um bloco de código nunca é dividido."""
    blocos: list[str] = []
    atual: list[str] = []
    em_cerca = False

    def fechar():
        texto = "\n".join(atual).strip()
        if texto:
            blocos.append(texto)
        atual.clear()

    for linha in linhas:
        if _CERCA.match(linha):
            em_cerca = not em_cerca
        if not linha.strip() and not em_cerca:
            fechar()
        else:
            atual.append(linha)
    fechar()
    return blocos

def _quebrar_longo(bloco: str, max_chars: int, sobreposicao: int) -> list[str]:
    """Divide um bloco maior que o limite em janelas, cortando em espaço, com sobreposição."""
    pedacos: list[str] = []
    inicio = 0
    while inicio < len(bloco):
        fim = min(inicio + max_chars, len(bloco))
        if fim < len(bloco):
            corte = bloco.rfind(" ", inicio + max_chars // 2, fim)
            fim = corte if corte != -1 else fim
        pedacos.append(bloco[inicio:fim].strip())
        if fim >= len(bloco):
            break
        inicio = max(fim - sobreposicao, inicio + 1)
    return [p for p in pedacos if p]

def _empacotar(blocos: list[str], max_chars: int, sobreposicao: int) -> list[str]:
    """Junta blocos vizinhos até o limite; blocos grandes demais são divididos."""
    trechos: list[str] = []
    atual = ""
    for bloco in blocos:
        if len(bloco) > max_chars:
            if atual:
                trechos.append(atual)
                atual = ""
            trechos.extend(_quebrar_longo(bloco, max_chars, sobreposicao))
        elif not atual:
            atual = bloco
        elif len(atual) + 2 + len(bloco) <= max_chars:
            atual += "\n\n" + bloco
        else:
            trechos.append(atual)
            atual = bloco
    if atual:
        trechos.append(atual)
    return trechos

def dividir_markdown(markdown: str, fonte: str, max_chars: int = 450, sobreposicao: int = 80) -> list[Trecho]:
    if max_chars < 50 or not 0 <= sobreposicao < max_chars // 2:
        raise ValueError("max_chars deve ser >= 50 e sobreposicao menor que metade de max_chars")
    resultado: list[Trecho] = []
    for secao, linhas in _secoes(markdown):
        for texto in _empacotar(_blocos(linhas), max_chars, sobreposicao):
            resultado.append(Trecho(fonte=fonte, secao=secao, texto=texto))
    return resultado
