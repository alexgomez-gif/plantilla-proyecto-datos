"""Bus de mensajes publicar/suscribir que comunica a los agentes."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Mensaje:
    tema: str
    emisor: str
    contenido: dict[str, Any]


@dataclass
class BusMensajes:
    """Entrega cada mensaje a todos los suscriptores de su tema y guarda el historial."""

    _suscriptores: dict[str, list[Callable[[Mensaje], None]]] = field(
        default_factory=lambda: defaultdict(list)
    )
    historial: list[Mensaje] = field(default_factory=list)

    def suscribir(self, tema: str, manejador: Callable[[Mensaje], None]) -> None:
        self._suscriptores[tema].append(manejador)

    def publicar(self, tema: str, emisor: str, contenido: dict[str, Any]) -> None:
        mensaje = Mensaje(tema, emisor, contenido)
        self.historial.append(mensaje)
        for manejador in list(self._suscriptores[tema]):
            manejador(mensaje)

    def contar(self, tema: str) -> int:
        return sum(1 for m in self.historial if m.tema == tema)
