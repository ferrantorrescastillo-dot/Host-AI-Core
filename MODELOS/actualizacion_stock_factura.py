from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class MovimientoStockFactura:
    articulo_id: str
    nombre_articulo: str
    cantidad: float
    unidad: str
    proveedor_id: str = ""
    proveedor_nombre: str = ""
    numero_factura: str = ""
    fecha_factura: str = ""
    precio_unitario: float = 0.0
    importe: float = 0.0
    ubicacion: str = ""
    lote: str = ""
    caducidad: str = ""
    origen_linea: Dict[str, Any] = field(default_factory=dict)
    accion_sugerida: str = "entrada_stock"
    requiere_revision: bool = False
    avisos: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("MOVSTFAC")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class InformeActualizacionStockFactura:
    movimientos: List[MovimientoStockFactura] = field(default_factory=list)
    total_movimientos: int = 0
    entradas_preparadas: int = 0
    requieren_revision: int = 0
    sin_articulo: int = 0
    cantidad_total_lineas: float = 0.0
    avisos_generales: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("INFSTFAC")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")
        self.recalcular()

    def recalcular(self):
        self.total_movimientos = len(self.movimientos)
        self.entradas_preparadas = sum(1 for m in self.movimientos if not m.requiere_revision and m.articulo_id)
        self.requieren_revision = sum(1 for m in self.movimientos if m.requiere_revision)
        self.sin_articulo = sum(1 for m in self.movimientos if not m.articulo_id)
        self.cantidad_total_lineas = round(sum(float(m.cantidad or 0) for m in self.movimientos), 4)

    def to_dict(self) -> Dict[str, Any]:
        self.recalcular()
        return {
            **asdict(self),
            "movimientos": [m.to_dict() for m in self.movimientos],
        }
