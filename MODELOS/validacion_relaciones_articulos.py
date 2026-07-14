from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class ValidacionRelacionArticulo:
    descripcion_factura: str
    articulo_id: str = ""
    nombre_articulo: str = ""
    valida: bool = True
    confianza: float = 0.0
    requiere_revision: bool = False
    errores: List[str] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)
    metodo: str = ""
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("VALRELART")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class InformeValidacionRelaciones:
    total_relaciones: int = 0
    validas: int = 0
    con_revision: int = 0
    invalidas: int = 0
    sin_articulo: int = 0
    puede_continuar: bool = False
    validaciones: List[ValidacionRelacionArticulo] = field(default_factory=list)
    avisos_generales: List[str] = field(default_factory=list)
    errores_generales: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("INFVALREL")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")
        self.recalcular()

    def recalcular(self):
        self.total_relaciones = len(self.validaciones)
        self.validas = sum(1 for v in self.validaciones if v.valida and not v.requiere_revision)
        self.con_revision = sum(1 for v in self.validaciones if v.valida and v.requiere_revision)
        self.invalidas = sum(1 for v in self.validaciones if not v.valida)
        self.sin_articulo = sum(1 for v in self.validaciones if not v.articulo_id)
        self.puede_continuar = self.invalidas == 0 and self.sin_articulo == 0

    def to_dict(self) -> Dict[str, Any]:
        self.recalcular()
        return {
            **asdict(self),
            "validaciones": [v.to_dict() for v in self.validaciones],
        }
