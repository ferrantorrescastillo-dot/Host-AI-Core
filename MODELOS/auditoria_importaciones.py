from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class RegistroAuditoriaImportacion:
    archivo: str
    estado: str  # preparado | aplicado | bloqueado | error
    proveedor_id: str = ""
    proveedor_nombre: str = ""
    total_lineas: int = 0
    relaciones_auto: int = 0
    precios_aplicados: int = 0
    stock_aplicado: int = 0
    requiere_revision: bool = False
    errores: List[str] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)
    resumen: str = ""
    datos: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("AUDIMP")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
