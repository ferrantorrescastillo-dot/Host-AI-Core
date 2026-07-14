from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class GestorContextoPermanente5410:
    """Estado conversacional de una sesión de Host AI.

    No escribe datos de negocio. Conserva únicamente el contexto operativo
    necesario para que respuestas cortas no vuelvan al clasificador general.
    """

    contexto: Dict[str, Any] = field(default_factory=dict)

    def activar_flujo(self, datos: Dict[str, Any]) -> None:
        self.contexto = deepcopy(datos)
        self.contexto["activo"] = True
        self.contexto.setdefault("estado_conversacion", "pendiente_confirmacion")
        self.contexto.setdefault("accion_seleccionada", None)
        self.contexto.setdefault("historial_estados", [])
        self._registrar(self.contexto["estado_conversacion"])

    def esta_activo(self) -> bool:
        return bool(self.contexto.get("activo"))

    def estado(self) -> str:
        return str(self.contexto.get("estado_conversacion") or "sin_contexto")

    def cambiar_estado(self, estado: str, **datos: Any) -> None:
        if not self.esta_activo():
            return
        self.contexto["estado_conversacion"] = estado
        self.contexto.update(datos)
        self._registrar(estado)

    def obtener(self, clave: Optional[str] = None, defecto: Any = None) -> Any:
        if clave is None:
            return self.contexto
        return self.contexto.get(clave, defecto)

    def snapshot(self) -> Dict[str, Any]:
        return deepcopy(self.contexto)

    def finalizar(self, motivo: str = "finalizado") -> Dict[str, Any]:
        anterior = self.snapshot()
        self.contexto.clear()
        return {"motivo": motivo, "contexto_anterior": anterior}

    def _registrar(self, estado: str) -> None:
        historial = self.contexto.setdefault("historial_estados", [])
        if not historial or historial[-1] != estado:
            historial.append(estado)


__all__ = ["GestorContextoPermanente5410"]
