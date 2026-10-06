"""
Validação da RESPOSTA do modelo: última camada, depois da geração.

- Remove segredos que o modelo possa ter reproduzido ou inventado no formato de
  uma credencial.
- Detecta vazamento do system prompt (cópia de longos trechos das instruções) e
  troca a resposta pela recusa padrão.
- Garante que nunca sai uma resposta vazia.
"""
from __future__ import annotations

from functools import lru_cache

from core.seguranca import CAT_PROMPT, RESPOSTAS, mascarar_segredos, normalizar

RESPOSTA_VAZIA = "Não consegui gerar uma resposta agora. Tente reformular a pergunta."

# Trecho copiado = sequência de TAMANHO_TRECHO palavras idênticas às do prompt.
# Parafrasear ("sigo regras de segurança") não casa; reproduzir o texto, sim.
_TAMANHO_TRECHO = 8
_TRECHOS_PARA_VAZAMENTO = 6


def _trechos(texto: str) -> set[tuple[str, ...]]:
    palavras = normalizar(texto).split()
    return {
        tuple(palavras[i:i + _TAMANHO_TRECHO])
        for i in range(len(palavras) - _TAMANHO_TRECHO + 1)
    }


@lru_cache(maxsize=4)
def _trechos_do_prompt(system_prompt: str) -> frozenset[tuple[str, ...]]:
    # As recusas-padrão fazem parte do prompt e o modelo as cita de propósito:
    # ficam de fora, senão toda recusa legítima pareceria vazamento.
    normalizado = normalizar(system_prompt)
    for frase in RESPOSTAS.values():
        normalizado = normalizado.replace(normalizar(frase), " ")
    return frozenset(_trechos(normalizado))


def vazou_prompt(resposta: str, system_prompt: str) -> bool:
    em_comum = _trechos(resposta) & _trechos_do_prompt(system_prompt)
    return len(em_comum) >= _TRECHOS_PARA_VAZAMENTO


def validar_resposta(resposta: str, system_prompt: str) -> str:
    """Devolve a resposta segura para entregar ao usuário."""
    resposta = (resposta or "").strip()
    if not resposta:
        return RESPOSTA_VAZIA
    if vazou_prompt(resposta, system_prompt):
        return RESPOSTAS[CAT_PROMPT]
    resposta, _ = mascarar_segredos(resposta)
    return resposta
