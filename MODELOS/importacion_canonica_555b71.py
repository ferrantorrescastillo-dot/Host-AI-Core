from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class FichaPlanImportacion555B71:
    codigo: str
    nombre: str
    accion: str
    motivo: str
    origen: str
    escandallo: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ResultadoImportacionCanonica555B71:
    modo: str
    ruta_preimportacion: str
    ruta_resolucion: str
    ruta_destino: str
    fichas: list[FichaPlanImportacion555B71] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)
    copia_seguridad: str | None = None
    diario_transaccion: str | None = None
    datos_reales_modificados: bool = False

    def to_dict(self) -> dict[str, Any]:
        resumen = {
            "analizadas": len(self.fichas),
            "crear": sum(1 for f in self.fichas if f.accion == "CREAR"),
            "actualizar": sum(1 for f in self.fichas if f.accion == "ACTUALIZAR"),
            "sin_cambios": sum(1 for f in self.fichas if f.accion == "SIN_CAMBIOS"),
            "omitidas": sum(1 for f in self.fichas if f.accion == "OMITIR"),
            "pendientes_confirmacion": sum(1 for f in self.fichas if f.accion == "PENDIENTE_CONFIRMACION"),
            "escritas": sum(1 for f in self.fichas if f.accion in {"CREAR", "ACTUALIZAR"})
            if self.datos_reales_modificados
            else 0,
        }
        return {
            "modo": self.modo,
            "ruta_preimportacion": self.ruta_preimportacion,
            "ruta_resolucion": self.ruta_resolucion,
            "ruta_destino": self.ruta_destino,
            "fichas": [f.to_dict() for f in self.fichas],
            "resumen": resumen,
            "errores": list(self.errores),
            "copia_seguridad": self.copia_seguridad,
            "diario_transaccion": self.diario_transaccion,
            "datos_reales_modificados": self.datos_reales_modificados,
        }
