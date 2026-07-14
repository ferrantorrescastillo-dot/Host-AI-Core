from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo): return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class RecomendacionCompra:
    tipo: str
    nivel: str
    mensaje: str
    accion_sugerida: str = ""
    articulo_id: str = ""
    proveedor_id: str = ""
    datos: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    creado_en: str = ""
    def __post_init__(self):
        if not self.id: self.id = nuevo_id("RECCOMP")
        if not self.creado_en: self.creado_en = datetime.now().isoformat(timespec="seconds")
    def to_dict(self): return asdict(self)
