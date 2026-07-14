from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class SolicitudPipeline:
    pipeline: str
    accion: str
    parametros: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    creado_en: str = ""
    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("REQ")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")
    def to_dict(self): return asdict(self)

@dataclass
class ResultadoPipeline:
    ok: bool
    pipeline: str
    accion: str
    mensaje: str
    datos: Dict[str, Any] = field(default_factory=dict)
    acciones_recomendadas: List[str] = field(default_factory=list)
    requiere_aprobacion: bool = False
    errores: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""
    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("RES")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")
    def to_dict(self): return asdict(self)
