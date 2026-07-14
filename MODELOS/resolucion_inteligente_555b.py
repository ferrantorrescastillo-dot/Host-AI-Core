from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class DecisionResolucion555B:
    grupo: str
    nombre: str
    tipo: str
    accion_propuesta: str
    confianza: float
    motivo: str
    fichas_origen: list[str] = field(default_factory=list)
    ficha_recomendada: str | None = None
    nombres_propuestos: list[str] = field(default_factory=list)
    requiere_confirmacion: bool = True
    detalles: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ResultadoResolucion555B:
    archivo_excel: str
    informe_preimportacion: str | None
    decisiones: list[DecisionResolucion555B] = field(default_factory=list)
    fichas_individuales: list[dict[str, Any]] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)
    datos_reales_modificados: bool = False

    def to_dict(self) -> dict[str, Any]:
        resumen = {
            "grupos_analizados": len(self.decisiones),
            "fusionar_duplicados": sum(1 for d in self.decisiones if d.accion_propuesta == "FUSIONAR_DUPLICADOS"),
            "mantener_variantes": sum(1 for d in self.decisiones if d.accion_propuesta == "MANTENER_COMO_VARIANTES"),
            "seleccionar_una": sum(1 for d in self.decisiones if d.accion_propuesta == "SELECCIONAR_MEJOR_FICHA"),
            "revisar_titulo": sum(1 for f in self.fichas_individuales if f.get("accion_propuesta") == "REVISAR_TITULO"),
            "listas_sin_confirmacion": sum(1 for d in self.decisiones if not d.requiere_confirmacion),
            "requieren_confirmacion": sum(1 for d in self.decisiones if d.requiere_confirmacion),
        }
        return {
            "archivo_excel": self.archivo_excel,
            "informe_preimportacion": self.informe_preimportacion,
            "decisiones": [d.to_dict() for d in self.decisiones],
            "fichas_individuales": list(self.fichas_individuales),
            "resumen": resumen,
            "errores": list(self.errores),
            "datos_reales_modificados": self.datos_reales_modificados,
        }
