from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid


def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"


@dataclass
class LineaFactura:
    """
    Línea estructurada de una factura.

    Ejemplo:
    Carrillera ternera | 8 kg | 8.45 €/kg | 67.60 €
    """
    descripcion: str
    cantidad: float = 0.0
    unidad: str = ""
    precio_unitario: float = 0.0
    importe: float = 0.0
    descuento: float = 0.0
    iva_porcentaje: float = 0.0
    codigo_proveedor: str = ""
    articulo_id_sugerido: str = ""
    proveedor_id: str = ""
    numero_factura: str = ""
    fecha_factura: str = ""
    confianza: float = 0.0
    origen_texto: str = ""
    avisos: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("LINFAC")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BloqueLineasFactura:
    """
    Resultado completo de extraer líneas de una factura.
    """
    archivo: str = ""
    proveedor_id: str = ""
    proveedor_nombre: str = ""
    numero_factura: str = ""
    fecha_factura: str = ""
    lineas: List[LineaFactura] = field(default_factory=list)
    lineas_descartadas: List[Dict[str, Any]] = field(default_factory=list)
    total_lineas: int = 0
    total_importe_lineas: float = 0.0
    total_factura_detectado: float = 0.0
    diferencia_total: float = 0.0
    confianza_media: float = 0.0
    avisos: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("BLOQLINFAC")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")
        self.recalcular()

    def recalcular(self):
        self.total_lineas = len(self.lineas)
        self.total_importe_lineas = round(sum(float(l.importe or 0) for l in self.lineas), 2)
        if self.total_factura_detectado:
            self.diferencia_total = round(self.total_factura_detectado - self.total_importe_lineas, 2)
        self.confianza_media = round(
            sum(float(l.confianza or 0) for l in self.lineas) / len(self.lineas),
            2
        ) if self.lineas else 0.0

    def to_dict(self) -> Dict[str, Any]:
        self.recalcular()
        return {
            **asdict(self),
            "lineas": [l.to_dict() for l in self.lineas],
        }


@dataclass
class ReglaLineaFactura:
    """
    Regla reutilizable para interpretar formatos de líneas por proveedor.
    """
    proveedor_id: str
    nombre: str
    patron: str
    descripcion: str = ""
    prioridad: int = 100
    activa: bool = True
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("REGLINFAC")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
