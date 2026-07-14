from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class RegistroHistoricoPrecio:
    articulo_id: str
    nombre_articulo: str
    precio: float
    unidad: str = ""
    proveedor_id: str = ""
    proveedor_nombre: str = ""
    numero_factura: str = ""
    fecha_factura: str = ""
    origen: str = "factura"
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("HISTPREC")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AnalisisHistoricoPrecio:
    articulo_id: str
    nombre_articulo: str
    total_registros: int = 0
    precio_minimo: float = 0.0
    precio_maximo: float = 0.0
    precio_medio: float = 0.0
    ultimo_precio: float = 0.0
    primer_precio: float = 0.0
    variacion_total: float = 0.0
    mejor_proveedor: str = ""
    peor_proveedor: str = ""
    tendencia: str = "estable"
    registros: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
