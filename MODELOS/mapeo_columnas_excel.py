from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class MapeoColumna:
    columna_original: str
    campo_canonico: str
    confianza: float
    origen: str = "automatico"  # automatico | aprendido | manual | desconocido
    motivos: List[str] = field(default_factory=list)
    tipo_detectado: str = ""
    letra: str = ""
    ejemplos: List[Any] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class MapeoHojaExcel:
    hoja: str
    tipo_documento: str = "desconocido"
    mapeos: List[MapeoColumna] = field(default_factory=list)
    desconocidas: List[Dict[str, Any]] = field(default_factory=list)
    obligatorias_faltantes: List[str] = field(default_factory=list)
    confianza_media: float = 0.0
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("MAPHOJA")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "mapeos": [m.to_dict() for m in self.mapeos],
        }

@dataclass
class MapeoDocumentoExcel:
    archivo: str
    nombre_archivo: str
    hojas: List[MapeoHojaExcel] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("MAPDOC")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "hojas": [h.to_dict() for h in self.hojas],
        }
