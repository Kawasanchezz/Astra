from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from string import Template

from rag.configuracao import PROMPTS_DIR

ARQUIVOS = ("sistema.md", "regra-contexto.md", "formato.md", "contexto.md")

@dataclass(frozen=True)
class Prompts:
    sistema: str
    regra: str
    formato: str
    contexto: Template
    versao: str

    @property
    def mensagem_sistema(self) -> str:
        return "\n\n".join((self.sistema, self.regra, self.formato))

    def mensagem_usuario(self, contexto: str, pergunta: str, marca: str = "") -> str:
        """O Template só substitui os marcadores do arquivo: um '$' na pergunta é texto comum."""
        return self.contexto.substitute(contexto=contexto, pergunta=pergunta, marca=marca)

def _ler(pasta: Path, nome: str) -> str:
    caminho = pasta / nome
    if not caminho.is_file():
        raise FileNotFoundError(f"prompt ausente: {caminho}")
    texto = caminho.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
    if not texto:
        raise ValueError(f"prompt vazio: {caminho}")
    return texto

def carregar_prompts(pasta: Path = PROMPTS_DIR) -> Prompts:
    """Lê os arquivos de prompts/. A versão é um hash do conteúdo (com quebras de linha
    normalizadas), então muda sozinha quando qualquer prompt muda e pode ir nos logs."""
    pasta = Path(pasta)
    textos = {nome: _ler(pasta, nome) for nome in ARQUIVOS}
    resumo = hashlib.sha256()
    for nome in ARQUIVOS:
        resumo.update(f"{nome}\0{textos[nome]}\0".encode())
    return Prompts(
        sistema=textos["sistema.md"],
        regra=textos["regra-contexto.md"],
        formato=textos["formato.md"],
        contexto=Template(textos["contexto.md"]),
        versao=resumo.hexdigest()[:10],
    )

@lru_cache(maxsize=1)
def prompts_padrao() -> Prompts:
    return carregar_prompts()
