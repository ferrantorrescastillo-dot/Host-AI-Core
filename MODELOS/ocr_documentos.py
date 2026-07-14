from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class DiagnosticoOCRDocumento:
    archivo: str
    nombre_archivo: str
    necesita_ocr: bool = False
    motivo: str = ""
    texto_actual: str = ""
    caracteres_detectados: int = 0
    paginas: int = 0
    confianza: float = 0.0
    recomendaciones: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("DIAGOCR")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
