from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class ItemAnalisisStock:
    clave: str
    nombre: str
    articulo_id: str = ""
    unidad: str = ""
    cantidad: float = 0.0
    stock_minimo: float = 0.0
    stock_maximo: float = 0.0
    valor_estimado: float = 0.0
    estado: str = "ok"
    ubicaciones: List[str] = field(default_factory=list)
    lotes: int = 0
    movimientos: int = 0
    dias_sin_movimiento: int = 0
    motivos: List[str] = field(default_factory=list)
    datos: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    creado_en: str = ""
    def __post_init__(self):
        if not self.id: self.id = nuevo_id("STKANA")
        if not self.creado_en: self.creado_en = datetime.now().isoformat(timespec="seconds")
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class InformeAnalisisInteligenteStock:
    total_articulos: int = 0
    total_lotes: int = 0
    valor_total_estimado: float = 0.0
    articulos_sin_stock: int = 0
    articulos_stock_bajo: int = 0
    articulos_exceso_stock: int = 0
    articulos_criticos: int = 0
    articulos_sin_movimiento: int = 0
    articulos_sin_ubicacion: int = 0
    items: List[Dict[str, Any]] = field(default_factory=list)
    resumen: Dict[str, Any] = field(default_factory=dict)
    lectura_host_ai: str = ""
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
