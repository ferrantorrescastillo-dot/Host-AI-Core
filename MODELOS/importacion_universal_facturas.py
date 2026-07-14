from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class PlanImportacionFactura:
    archivo: str
    tipo_archivo: str = ""
    necesita_ocr: bool = False
    pasos: List[str] = field(default_factory=list)
    puede_importar: bool = False
    requiere_revision: bool = True
    avisos: List[str] = field(default_factory=list)
    datos_previos: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("PLANIMPFAC")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ResultadoImportacionUniversalFactura:
    archivo: str
    ok: bool = False
    plan: Dict[str, Any] = field(default_factory=dict)
    lectura: Dict[str, Any] = field(default_factory=dict)
    validacion_lineas: Dict[str, Any] = field(default_factory=dict)
    relaciones: Dict[str, Any] = field(default_factory=dict)
    validacion_relaciones: Dict[str, Any] = field(default_factory=dict)
    informe_precios: Dict[str, Any] = field(default_factory=dict)
    informe_stock: Dict[str, Any] = field(default_factory=dict)
    requiere_revision: bool = True
    errores: List[str] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("RESIMPFAC")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
