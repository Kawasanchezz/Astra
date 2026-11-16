import re
from pathlib import Path

import pytest

from services.ia_service import sanitizar_input

RAIZ = Path(__file__).resolve().parent.parent
DOCKERFILES = ["Dockerfile.rag", "ai-gateway-java/Dockerfile"]
INVISIVEIS = re.compile("[​-‏‪-‮⁦-⁩﻿]")


def linhas_de(arquivo):
    return [x.strip() for x in (RAIZ / arquivo).read_text(encoding="utf-8").splitlines()]


def lock_pacotes():
    texto = (RAIZ / "requirements-rag.lock").read_text(encoding="utf-8")
    blocos = re.split(r"\n(?=[A-Za-z0-9_.-]+==)", texto)
    return [b for b in blocos if re.match(r"[A-Za-z0-9_.-]+==", b)]


def test_lock_fixa_versao_exata_e_hash_em_todo_pacote():
    pacotes = lock_pacotes()
    assert len(pacotes) > 30
    for bloco in pacotes:
        assert re.match(r"[A-Za-z0-9_.-]+==[\w.]+", bloco), bloco[:40]
        assert "--hash=sha256:" in bloco, bloco[:40]


def test_lock_cobre_toda_dependencia_declarada_e_nao_traz_ferramenta_de_dev():
    nomes = {b.split("==")[0].lower().replace("_", "-") for b in lock_pacotes()}
    for arquivo in ("requirements.txt", "requirements-rag.txt"):
        for linha in linhas_de(arquivo):
            limpa = linha.split("#")[0].split(";")[0].strip()
            if limpa and not limpa.startswith("-r"):
                assert re.split(r"[<>=!~ ]", limpa)[0].lower() in nomes, limpa
    assert not nomes & {"pytest", "ruff", "mypy", "bandit", "pip-audit", "playwright"}


@pytest.mark.parametrize("arquivo", DOCKERFILES)
def test_dockerfile_usa_base_por_digest(arquivo):
    imagens = [x.split()[1] for x in linhas_de(arquivo) if x.upper().startswith("FROM ")]
    assert imagens and all(re.search(r"@sha256:[0-9a-f]{64}$", i) for i in imagens), imagens


@pytest.mark.parametrize("arquivo", DOCKERFILES)
def test_imagem_final_roda_sem_root_e_sem_segredo_embutido(arquivo):
    linhas = linhas_de(arquivo)
    usuarios = [x.split()[1] for x in linhas if x.upper().startswith("USER ")]
    assert usuarios and usuarios[-1] not in ("root", "0")
    for linha in linhas:
        if re.match(r"(ENV|ARG)\s", linha, re.I):
            assert not re.search(r"(KEY|TOKEN|SECRET|PASSWORD)", linha, re.I), linha
    assert not any(re.match(r"COPY\s+.*\.env(\s|$)", x) for x in linhas)


def test_imagem_python_instala_so_com_hash():
    instalacao = [x for x in linhas_de("Dockerfile.rag") if "pip install" in x]
    assert instalacao and all("--require-hashes" in x and "requirements-rag.lock" in x for x in instalacao)


def test_dockerignore_barra_env_e_chaves():
    regras = linhas_de(".dockerignore")
    assert "**/.env" in regras and "**/.env.*" in regras and "!**/.env.example" in regras


def test_dependabot_cobre_pip_maven_docker_e_actions():
    texto = (RAIZ / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    for ecossistema in ("pip", "maven", "docker", "github-actions"):
        assert f"package-ecosystem: {ecossistema}" in texto
    assert texto.count("package-ecosystem: docker") == 2


def arquivos_de_codigo():
    pastas = [RAIZ / "servidor", RAIZ / "landing-page" / "js", RAIZ / "ai-gateway-java" / "src" / "main"]
    for pasta in pastas:
        for caminho in pasta.rglob("*"):
            if caminho.suffix in (".py", ".js", ".java") and ".cache" not in caminho.parts:
                yield caminho
    yield RAIZ / "app.py"


def test_codigo_nao_tem_caractere_invisivel_ou_bidi_literal():
    achados = [str(c.relative_to(RAIZ)) for c in arquivos_de_codigo()
               if INVISIVEIS.search(c.read_text(encoding="utf-8", errors="ignore"))]
    assert achados == []


def test_sanitizador_continua_removendo_invisiveis_e_bidi():
    sujo = "o​i‏ ‪tudo‮﻿ bem"
    assert sanitizar_input(sujo) == "oi tudo bem"
