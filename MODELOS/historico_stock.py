from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class RegistroHistoricoStock:
    articulo_id: str
    nombre_articulo: str
    tipo: str  # entrada | salida | ajuste
    cantidad: float
    unidad: str
    stock_resultante: float = 0.0
    proveedor_id: str = ""
    numero_factura: str = ""
    fecha_factura: str = ""
    motivo: str = ""
    origen: str = "factura"
    datos: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("HISTSTOCK")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AnalisisHistoricoStock:
    articulo_id: str
    nombre_articulo: str
    total_registros: int = 0
    entradas_totales: float = 0.0
    salidas_totales: float = 0.0
    ajustes_totales: float = 0.0
    stock_estimado: float = 0.0
    unidad_principal: str = ""
    registros: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
