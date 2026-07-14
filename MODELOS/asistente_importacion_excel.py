from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class PasoImportacionExcel:
    nombre: str
    estado: str = "pendiente"  # pendiente | ok | revisar | error | saltado
    mensaje: str = ""
    datos: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SesionImportacionExcel:
    archivo: str
    tipo_detectado: str = "desconocido"
    confianza: float = 0.0
    estado: str = "iniciada"  # iniciada | lista_para_importar | bloqueada | importada
    pasos: List[PasoImportacionExcel] = field(default_factory=list)
    importadores_sugeridos: List[str] = field(default_factory=list)
    resultado_importacion: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("SESIMP")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "pasos": [p.to_dict() for p in self.pasos],
        }
