from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class NecesidadProduccion:
    receta_id: str
    nombre: str
    cantidad: float
    unidad: str
    origen: str = "evento"
    pase: str = ""
    prioridad: int = 80
    id: str = ""
    creado_en: str = ""
    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("NECPROD")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class InformeProduccionCompleta:
    evento_id: str
    evento: str
    necesidades: List[Dict[str, Any]] = field(default_factory=list)
    predicciones_stock: List[Dict[str, Any]] = field(default_factory=list)
    compras_generadas: List[Dict[str, Any]] = field(default_factory=list)
    simulacion: Dict[str, Any] = field(default_factory=dict)
    estado: str = "borrador"
    avisos: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""
    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("INFPROD")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
