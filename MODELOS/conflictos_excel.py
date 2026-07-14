from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class ConflictoExcel:
    tipo: str
    nivel: str
    mensaje: str
    entidad: str = ""
    entidad_id: str = ""
    datos: Dict[str, Any] = field(default_factory=dict)
    opciones: List[str] = field(default_factory=list)
    recomendacion: str = ""
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("CONF")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class InformeConflictosExcel:
    archivo: str
    modo: str = "analisis"
    conflictos: List[ConflictoExcel] = field(default_factory=list)
    total_conflictos: int = 0
    criticos: int = 0
    avisos: int = 0
    informativos: int = 0
    puede_importar: bool = True
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("INFCONF")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "conflictos": [c.to_dict() for c in self.conflictos],
        }
