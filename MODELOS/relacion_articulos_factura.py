from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid


def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"


@dataclass
class CandidatoArticuloFactura:
    articulo_id: str
    nombre_articulo: str
    confianza: float = 0.0
    metodo: str = "desconocido"
    motivos: List[str] = field(default_factory=list)
    proveedor_id: str = ""
    unidad: str = ""
    familia: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RelacionLineaArticulo:
    descripcion_factura: str
    cantidad: float = 0.0
    unidad: str = ""
    precio_unitario: float = 0.0
    importe: float = 0.0
    proveedor_id: str = ""
    articulo_id: str = ""
    nombre_articulo: str = ""
    confianza: float = 0.0
    metodo: str = "sin_relacion"
    requiere_revision: bool = True
    candidatos: List[CandidatoArticuloFactura] = field(default_factory=list)
    decision_usuario: str = ""
    avisos: List[str] = field(default_factory=list)
    origen_linea: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("RELLINART")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "candidatos": [c.to_dict() for c in self.candidatos],
        }


@dataclass
class InformeRelacionArticulosFactura:
    archivo: str = ""
    proveedor_id: str = ""
    proveedor_nombre: str = ""
    numero_factura: str = ""
    fecha_factura: str = ""
    relaciones: List[RelacionLineaArticulo] = field(default_factory=list)
    total_lineas: int = 0
    relacionadas_auto: int = 0
    requieren_revision: int = 0
    sin_relacion: int = 0
    confianza_media: float = 0.0
    puede_continuar: bool = False
    avisos_generales: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("INFRELART")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")
        self.recalcular()

    def recalcular(self):
        self.total_lineas = len(self.relaciones)
        self.relacionadas_auto = sum(1 for r in self.relaciones if r.articulo_id and not r.requiere_revision)
        self.requieren_revision = sum(1 for r in self.relaciones if r.requiere_revision and r.articulo_id)
        self.sin_relacion = sum(1 for r in self.relaciones if not r.articulo_id)
        self.confianza_media = round(
            sum(float(r.confianza or 0) for r in self.relaciones) / len(self.relaciones),
            2
        ) if self.relaciones else 0.0
        self.puede_continuar = self.sin_relacion == 0

    def to_dict(self) -> Dict[str, Any]:
        self.recalcular()
        return {
            **asdict(self),
            "relaciones": [r.to_dict() for r in self.relaciones],
        }


@dataclass
class AprendizajeRelacionProveedor:
    proveedor_id: str
    texto_proveedor: str
    articulo_id: str
    nombre_articulo: str
    confianza: float = 100.0
    usos: int = 0
    id: str = ""
    creado_en: str = ""
    actualizado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("APRRELPROV")
        ahora = datetime.now().isoformat(timespec="seconds")
        if not self.creado_en:
            self.creado_en = ahora
        if not self.actualizado_en:
            self.actualizado_en = ahora

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
