from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid


def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"


@dataclass
class LineaEscandallo:
    nombre: str
    cantidad: float
    unidad: str
    tipo: str = "articulo"  # articulo | elaboracion
    articulo_id: str = ""
    elaboracion_id: str = ""
    merma_porcentaje: float = 0.0
    familia: str = ""
    proveedor_preferente: str = ""
    coste_unitario: float = 0.0
    notas: str = ""
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("LINESC")

    def cantidad_bruta(self) -> float:
        merma = max(0.0, float(self.merma_porcentaje or 0.0))
        return round(float(self.cantidad or 0.0) * (1 + merma / 100), 4)

    def coste_total(self) -> float:
        return round(self.cantidad_bruta() * float(self.coste_unitario or 0.0), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "cantidad_bruta": self.cantidad_bruta(),
            "coste_total": self.coste_total(),
        }


@dataclass
class EscandalloReceta:
    receta_id: str
    nombre: str
    raciones_base: int
    lineas: List[LineaEscandallo] = field(default_factory=list)
    grupo: str = ""
    subgrupo: str = ""
    observaciones: str = ""
    activo: bool = True
    id: str = ""
    creado_en: str = ""
    actualizado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("ESC")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")
        if not self.actualizado_en:
            self.actualizado_en = self.creado_en

    def coste_total_base(self) -> float:
        return round(sum(l.coste_total() for l in self.lineas), 4)

    def coste_por_racion(self) -> float:
        if not self.raciones_base:
            return 0.0
        return round(self.coste_total_base() / self.raciones_base, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "lineas": [l.to_dict() for l in self.lineas],
            "coste_total_base": self.coste_total_base(),
            "coste_por_racion": self.coste_por_racion(),
        }


@dataclass
class NecesidadEscandallo:
    receta_id: str
    receta: str
    nombre: str
    cantidad_neta: float
    cantidad_bruta: float
    unidad: str
    tipo: str = "articulo"
    articulo_id: str = ""
    elaboracion_id: str = ""
    familia: str = ""
    proveedor_preferente: str = ""
    coste_estimado: float = 0.0
    origen: str = ""
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("NECESC")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
