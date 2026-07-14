from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid


def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"


@dataclass
class PrecioArticulo:
    nombre: str
    precio_unitario: float
    unidad: str
    articulo_id: str = ""
    proveedor: str = ""
    familia: str = ""
    fecha: str = ""
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("PRECIO")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")
        if not self.fecha:
            self.fecha = datetime.now().date().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CosteLinea:
    nombre: str
    cantidad: float
    unidad: str
    precio_unitario: float
    coste_total: float
    tipo: str = "articulo"
    articulo_id: str = ""
    elaboracion_id: str = ""
    proveedor: str = ""
    familia: str = ""
    origen: str = ""
    notas: str = ""
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("COSTLIN")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CosteReceta:
    receta_id: str
    receta: str
    raciones: int
    lineas: List[CosteLinea] = field(default_factory=list)
    coste_total: float = 0.0
    coste_por_racion: float = 0.0
    precio_venta_por_racion: float = 0.0
    margen_bruto: float = 0.0
    food_cost_porcentaje: float = 0.0
    estado: str = "calculado"
    avisos: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("COSTREC")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return {**asdict(self), "lineas": [l.to_dict() for l in self.lineas]}


@dataclass
class CosteEvento:
    evento_id: str
    evento: str
    pax: int
    recetas: List[Dict[str, Any]] = field(default_factory=list)
    extras: List[CosteLinea] = field(default_factory=list)
    coste_materia_prima: float = 0.0
    coste_extras: float = 0.0
    coste_total: float = 0.0
    coste_por_pax: float = 0.0
    precio_venta_total: float = 0.0
    precio_venta_por_pax: float = 0.0
    margen_bruto: float = 0.0
    beneficio_estimado: float = 0.0
    food_cost_porcentaje: float = 0.0
    estado: str = "calculado"
    avisos: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("COSTEVT")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return {**asdict(self), "extras": [e.to_dict() for e in self.extras]}


@dataclass
class SimulacionPrecio:
    objetivo: str
    variacion_porcentaje: float
    antes: Dict[str, Any]
    despues: Dict[str, Any]
    impacto: Dict[str, Any]
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("SIMCOST")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
