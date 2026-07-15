from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Dict, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class LoteStock:
    nombre: str
    cantidad: float
    unidad: str
    familia: str = ""
    ubicacion: str = ""
    proveedor: str = ""
    articulo_id: str = ""
    fecha_entrada: str = ""
    caducidad: str = ""
    coste_unitario: float = 0.0
    id: str = ""
    creado_en: str = ""
    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("LOTE")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")
        if not self.fecha_entrada:
            self.fecha_entrada = datetime.now().date().isoformat()
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class MovimientoStock:
    tipo: str
    nombre: str
    cantidad: float
    unidad: str
    motivo: str = ""
    lote_id: str = ""
    articulo_id: str = ""
    trazabilidad: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    creado_en: str = ""
    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("MOV")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
