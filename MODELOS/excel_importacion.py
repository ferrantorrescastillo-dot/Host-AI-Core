from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid


def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"


@dataclass
class ColumnaExcel:
    indice: int
    letra: str
    nombre_detectado: str
    tipo_detectado: str = "desconocido"
    total_celdas: int = 0
    celdas_con_dato: int = 0
    porcentaje_vacio: float = 0.0
    ejemplos: List[Any] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HojaExcel:
    nombre: str
    filas: int
    columnas: int
    celdas_utilizadas: int
    columnas_detectadas: List[ColumnaExcel] = field(default_factory=list)
    vista_previa: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "columnas_detectadas": [c.to_dict() for c in self.columnas_detectadas],
        }


@dataclass
class AnalisisExcel:
    archivo: str
    nombre_archivo: str
    hojas: List[HojaExcel] = field(default_factory=list)
    total_hojas: int = 0
    total_filas: int = 0
    total_columnas: int = 0
    total_celdas_utilizadas: int = 0
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("ANEXCEL")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "hojas": [h.to_dict() for h in self.hojas],
        }
