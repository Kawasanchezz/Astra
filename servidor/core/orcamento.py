import math
import threading
import time
from collections.abc import Callable

from config import ORCAMENTO_DIARIO_TOKENS

SEGUNDOS_POR_DIA = 86400
BYTES_POR_TOKEN_ESTIMADO = 3


def estimar_tokens(texto: str) -> int:
    return math.ceil(len(texto.encode("utf-8")) / BYTES_POR_TOKEN_ESTIMADO)


class OrcamentoDiario:
    def __init__(self, limite: int, relogio: Callable[[], float] = time.time):
        self._limite = limite
        self._relogio = relogio
        self._trava = threading.Lock()
        self._dia = self._dia_atual()
        self._usado = 0

    def _dia_atual(self) -> int:
        return int(self._relogio() // SEGUNDOS_POR_DIA)

    def _virar_o_dia(self) -> None:
        dia = self._dia_atual()
        if dia != self._dia:
            self._dia = dia
            self._usado = 0

    @property
    def usado(self) -> int:
        with self._trava:
            self._virar_o_dia()
            return self._usado

    def reservar(self, tokens: int) -> bool:
        if self._limite <= 0:
            return True
        with self._trava:
            self._virar_o_dia()
            if self._usado + tokens > self._limite:
                return False
            self._usado += tokens
            return True

    def acertar(self, reservado: int, real: int | None) -> None:
        if self._limite <= 0:
            return
        gasto = reservado if real is None else real
        with self._trava:
            self._virar_o_dia()
            self._usado = max(0, self._usado - reservado + gasto)

    def segundos_ate_reiniciar(self) -> int:
        return int(SEGUNDOS_POR_DIA - self._relogio() % SEGUNDOS_POR_DIA) + 1


orcamento_diario = OrcamentoDiario(ORCAMENTO_DIARIO_TOKENS)
