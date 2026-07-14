from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class ProveedorPDF:
    proveedor_id: str
    nombre_normalizado: str
    nombres: List[str] = field(default_factory=list)
    cifs: List[str] = field(default_factory=list)
    dominios: List[str] = field(default_factory=list)
    palabras_clave: List[str] = field(default_factory=list)
    categoria: str = ""
    origen: str = "diccionario"
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class DeteccionProveedorPDF:
    proveedor_id: str = ""
    nombre: str = ""
    confianza: float = 0.0
    metodo: str = "desconocido"
    coincidencias: List[str] = field(default_factory=list)
    candidatos: List[Dict[str, Any]] = field(default_factory=list)
    requiere_aprendizaje: bool = False
    avisos: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""
    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("DETPROV")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
