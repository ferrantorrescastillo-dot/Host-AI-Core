from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class PaginaPDF:
    numero: int
    texto: str = ""
    caracteres: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AnalisisPDF:
    archivo: str
    nombre_archivo: str
    paginas: List[PaginaPDF] = field(default_factory=list)
    texto_completo: str = ""
    total_paginas: int = 0
    total_caracteres: int = 0
    metodo_extraccion: str = "desconocido"
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("ANPDF")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "paginas": [p.to_dict() for p in self.paginas],
        }

@dataclass
class DeteccionFacturaPDF:
    proveedor: str = ""
    cif: str = ""
    numero_factura: str = ""
    fecha: str = ""
    total: float = 0.0
    base_imponible: float = 0.0
    iva: float = 0.0
    confianza: float = 0.0
    avisos: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
