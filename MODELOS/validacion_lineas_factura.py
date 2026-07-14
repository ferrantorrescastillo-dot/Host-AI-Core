from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid


def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"


@dataclass
class ValidacionLineaFactura:
    descripcion: str
    valida: bool = True
    errores: List[str] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)
    confianza_original: float = 0.0
    confianza_validacion: float = 100.0
    cantidad: float = 0.0
    unidad: str = ""
    precio_unitario: float = 0.0
    importe: float = 0.0
    importe_calculado: float = 0.0
    diferencia: float = 0.0
    origen_texto: str = ""
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("VALLINFAC")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InformeValidacionFactura:
    archivo: str = ""
    total_lineas: int = 0
    lineas_validas: int = 0
    lineas_con_avisos: int = 0
    lineas_invalidas: int = 0
    importe_lineas: float = 0.0
    total_factura_detectado: float = 0.0
    diferencia_total: float = 0.0
    confianza_media: float = 0.0
    puede_importar: bool = True
    validaciones: List[ValidacionLineaFactura] = field(default_factory=list)
    duplicados: List[Dict[str, Any]] = field(default_factory=list)
    avisos_generales: List[str] = field(default_factory=list)
    errores_generales: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("INFVALLINFAC")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def recalcular(self):
        self.total_lineas = len(self.validaciones)
        self.lineas_validas = sum(1 for v in self.validaciones if v.valida and not v.avisos)
        self.lineas_con_avisos = sum(1 for v in self.validaciones if v.valida and v.avisos)
        self.lineas_invalidas = sum(1 for v in self.validaciones if not v.valida)
        self.importe_lineas = round(sum(float(v.importe or 0) for v in self.validaciones), 2)
        if self.total_factura_detectado:
            self.diferencia_total = round(self.total_factura_detectado - self.importe_lineas, 2)
        self.confianza_media = round(
            sum(float(v.confianza_validacion or 0) for v in self.validaciones) / len(self.validaciones),
            2
        ) if self.validaciones else 0.0
        self.puede_importar = self.lineas_invalidas == 0 and not self.errores_generales

    def to_dict(self) -> Dict[str, Any]:
        self.recalcular()
        return {
            **asdict(self),
            "validaciones": [v.to_dict() for v in self.validaciones],
        }
