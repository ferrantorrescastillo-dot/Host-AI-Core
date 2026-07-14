from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class DiferenciaReconciliacionStock:
    clave: str
    nombre: str
    articulo_id: str = ""
    unidad: str = ""
    stock_teorico: float = 0.0
    stock_real: float = 0.0
    diferencia: float = 0.0
    porcentaje_diferencia: float = 0.0
    gravedad: str = "informativa"
    causa_probable: str = ""
    accion_recomendada: str = ""
    datos: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    creado_en: str = ""
    def __post_init__(self):
        if not self.id: self.id = nuevo_id("RECSTK")
        if not self.creado_en: self.creado_en = datetime.now().isoformat(timespec="seconds")
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class InformeReconciliacionStock:
    total_articulos: int = 0
    total_diferencias: int = 0
    diferencias_criticas: int = 0
    diferencias_aviso: int = 0
    diferencias_informativas: int = 0
    valor_diferencia_estimado: float = 0.0
    diferencias: List[Dict[str, Any]] = field(default_factory=list)
    resumen: Dict[str, Any] = field(default_factory=dict)
    lectura_host_ai: str = ""
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
