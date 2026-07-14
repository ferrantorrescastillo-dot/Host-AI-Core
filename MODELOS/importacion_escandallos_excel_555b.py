from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(slots=True)
class HojaEscandallosDetectada:
    nombre: str
    fila_cabecera: int
    columnas: list[str]
    filas_con_datos: int
    vista_previa: list[dict[str, Any]] = field(default_factory=list)
    mapeo_sugerido: dict[str, str] = field(default_factory=dict)
    campos_faltantes: list[str] = field(default_factory=list)
    confianza: float = 0.0
    candidata_escandallos: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ResultadoVistaPreviaExcel555B:
    archivo: str
    hojas: list[HojaEscandallosDetectada] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    modo: str = "solo_lectura"

    @property
    def hojas_candidatas(self) -> int:
        return sum(1 for hoja in self.hojas if hoja.candidata_escandallos)

    def to_dict(self) -> dict[str, Any]:
        return {
            "archivo": self.archivo,
            "hojas": [hoja.to_dict() for hoja in self.hojas],
            "hojas_candidatas": self.hojas_candidatas,
            "errores": list(self.errores),
            "avisos": list(self.avisos),
            "modo": self.modo,
            "datos_reales_modificados": False,
        }
