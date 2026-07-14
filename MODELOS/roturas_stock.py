from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class PrediccionRoturaStock:
    articulo_id: str
    nombre_articulo: str
    stock_actual: float
    consumo_medio: float
    dias_hasta_rotura: float
    fecha_estimada_rotura: str
    nivel_riesgo: str
    recomendacion: str
    unidad: str = ""
    proveedor_id: str = ""
    confianza: str = "media"
    datos: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    creado_en: str = ""
    def __post_init__(self):
        if not self.id: self.id = nuevo_id("ROTSTOCK")
        if not self.creado_en: self.creado_en = datetime.now().isoformat(timespec="seconds")
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class InformeRoturasStock:
    total_articulos: int = 0
    criticas: int = 0
    avisos: int = 0
    estables: int = 0
    predicciones: List[Dict[str, Any]] = field(default_factory=list)
    lectura_host_ai: str = ""
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
