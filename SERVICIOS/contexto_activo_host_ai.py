from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


CONTEXT_GENERAL = "GENERAL"
CONTEXT_EVENTO = "EVENTO"
CONTEXT_RECETA = "RECETA"
CONTEXT_ESCANDALLO = "ESCANDALLO"
CONTEXT_MENU = "MENU"
CONTEXT_PRODUCCION = "PRODUCCION"


@dataclass
class ContextoActivoHostAI:
    tipo: str = CONTEXT_GENERAL
    entidad_id: str = ""
    etiqueta: str = "Contexto general"
    origen: str = "shell"
    estado: str = "activo"
    metadatos: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["metadatos"] = dict(self.metadatos or {})
        return data


class ServicioContextoActivoHostAI:
    """Contrato de contexto activo independiente de la UI concreta."""

    def __init__(self) -> None:
        self._contexto = ContextoActivoHostAI()

    def obtener(self) -> ContextoActivoHostAI:
        return ContextoActivoHostAI(**self._contexto.to_dict())

    def establecer_general(self) -> ContextoActivoHostAI:
        self._contexto = ContextoActivoHostAI()
        return self.obtener()

    def establecer(self, tipo: str, entidad_id: str = "", etiqueta: str = "", origen: str = "shell", metadatos: dict[str, Any] | None = None) -> ContextoActivoHostAI:
        tipo_norm = str(tipo or CONTEXT_GENERAL).strip().upper()
        label = etiqueta.strip() if etiqueta else f"Contexto {tipo_norm.lower()}"
        self._contexto = ContextoActivoHostAI(
            tipo=tipo_norm,
            entidad_id=str(entidad_id or ""),
            etiqueta=label,
            origen=str(origen or "shell"),
            estado="activo",
            metadatos=dict(metadatos or {}),
        )
        return self.obtener()


__all__ = [
    "ContextoActivoHostAI",
    "ServicioContextoActivoHostAI",
    "CONTEXT_GENERAL",
    "CONTEXT_EVENTO",
    "CONTEXT_RECETA",
    "CONTEXT_ESCANDALLO",
    "CONTEXT_MENU",
    "CONTEXT_PRODUCCION",
]
