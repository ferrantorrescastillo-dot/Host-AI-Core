from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class LineaControlMovimientoStock:
    tipo: str
    nombre: str
    articulo_id: str = ""
    unidad: str = ""
    cantidad: float = 0.0
    motivo: str = ""
    lote_id: str = ""
    fecha: str = ""
    gravedad: str = "informativa"
    observaciones: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""
    def __post_init__(self):
        if not self.id: self.id = nuevo_id("MOVSTK")
        if not self.creado_en: self.creado_en = datetime.now().isoformat(timespec="seconds")
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class InformeControlMovimientosStock:
    total_movimientos: int = 0
    total_entradas: int = 0
    total_salidas: int = 0
    total_ajustes: int = 0
    total_mermas: int = 0
    total_descuadres: int = 0
    cantidad_entrada_total: float = 0.0
    cantidad_salida_total: float = 0.0
    movimientos: List[Dict[str, Any]] = field(default_factory=list)
    resumen_por_articulo: Dict[str, Any] = field(default_factory=dict)
    resumen: Dict[str, Any] = field(default_factory=dict)
    lectura_host_ai: str = ""
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
