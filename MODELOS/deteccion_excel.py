from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid


def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"


@dataclass
class TipoDocumentoDetectado:
    tipo: str
    confianza: float
    motivos: List[str] = field(default_factory=list)
    columnas_clave_detectadas: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DeteccionHojaExcel:
    hoja: str
    filas: int
    columnas: int
    tipo_principal: str
    confianza: float
    candidatos: List[TipoDocumentoDetectado] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "candidatos": [c.to_dict() for c in self.candidatos],
        }


@dataclass
class DeteccionDocumentoExcel:
    archivo: str
    nombre_archivo: str
    tipo_principal: str
    confianza: float
    hojas: List[DeteccionHojaExcel] = field(default_factory=list)
    resumen: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("DETEXCEL")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "hojas": [h.to_dict() for h in self.hojas],
        }
