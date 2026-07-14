from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List

@dataclass
class ResumenUbicacionStock:
    ubicacion: str
    total_articulos: int = 0
    total_lotes: int = 0
    cantidad_total: float = 0.0
    valor_estimado: float = 0.0
    articulos: List[Dict[str, Any]] = field(default_factory=list)
    alertas: List[Dict[str, Any]] = field(default_factory=list)
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class MovimientoUbicacionStock:
    nombre: str
    articulo_id: str = ''
    origen: str = ''
    destino: str = ''
    cantidad: float = 0.0
    unidad: str = ''
    lote_id: str = ''
    ok: bool = True
    mensaje: str = ''
    datos: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class InformeStockUbicaciones:
    total_ubicaciones: int
    total_articulos: int
    total_lotes: int
    valor_total_estimado: float
    ubicaciones: List[Dict[str, Any]]
    sin_ubicacion: List[Dict[str, Any]]
    alertas: List[Dict[str, Any]]
    resumen: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
