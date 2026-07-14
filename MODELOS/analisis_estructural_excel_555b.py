from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class BloqueFichaDetectado555B:
    fila_inicio: int
    fila_fin: int
    titulo: str
    filas_con_datos: int
    confianza: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class HojaClasificada555B:
    nombre: str
    tipo: str
    confianza: float
    motivos: list[str] = field(default_factory=list)
    bloques: list[BloqueFichaDetectado555B] = field(default_factory=list)
    hoja_relacionada: str | None = None
    accion_recomendada: str = "REVISAR"

    def to_dict(self) -> dict[str, Any]:
        datos = asdict(self)
        datos["bloques"] = [bloque.to_dict() for bloque in self.bloques]
        return datos


@dataclass(slots=True)
class ResultadoAnalisisEstructural555B:
    archivo: str
    hojas: list[HojaClasificada555B] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        conteo: dict[str, int] = {}
        for hoja in self.hojas:
            conteo[hoja.tipo] = conteo.get(hoja.tipo, 0) + 1
        return {
            "archivo": self.archivo,
            "hojas": [hoja.to_dict() for hoja in self.hojas],
            "resumen_tipos": conteo,
            "bloques_detectados": sum(len(hoja.bloques) for hoja in self.hojas),
            "errores": list(self.errores),
            "avisos": list(self.avisos),
            "modo": "solo_lectura",
            "datos_reales_modificados": False,
        }
