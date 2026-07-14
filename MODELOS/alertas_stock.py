from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class AlertaStock:
    articulo_id: str
    nombre_articulo: str
    tipo: str
    nivel: str
    mensaje: str
    stock_actual: float = 0.0
    unidad: str = ""
    stock_minimo: float = 0.0
    accion_sugerida: str = ""
    datos: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("ALSTOCK")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
