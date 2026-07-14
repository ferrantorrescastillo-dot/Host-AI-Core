from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class ErrorImportacionEscandallo:
    hoja: str
    fila: int
    mensaje: str
    datos: Dict[str, Any] = field(default_factory=dict)
    nivel: str = "error"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ResultadoImportacionEscandallos:
    archivo: str
    escandallos_importados: int = 0
    recetas_detectadas: int = 0
    lineas_importadas: int = 0
    articulos_detectados: int = 0
    errores: List[ErrorImportacionEscandallo] = field(default_factory=list)
    escandallos: List[Dict[str, Any]] = field(default_factory=list)
    modo: str = "vista_previa"  # vista_previa | importar
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("IMPESC")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "errores": [e.to_dict() for e in self.errores],
        }
