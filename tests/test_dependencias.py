import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
REQUISITOS = ["requirements.txt", "requirements-rag.txt"]


def dependencias(arquivo):
    for linha in (RAIZ / arquivo).read_text(encoding="utf-8").splitlines():
        limpa = linha.split("#")[0].strip()
        if limpa and not limpa.startswith("-r"):
            yield limpa


@pytest.mark.parametrize("arquivo", REQUISITOS)
def test_toda_dependencia_tem_versao_minima_e_teto(arquivo):
    sem_limite = [
        d for d in dependencias(arquivo)
        if not re.search(r"==\s*[\d.]+", d) and not (re.search(r">=\s*[\d.]+", d) and re.search(r"<\s*[\d.]+", d))
    ]
    assert sem_limite == []
