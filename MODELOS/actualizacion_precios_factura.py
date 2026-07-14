from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class CambioPrecioFactura:
    articulo_id: str
    nombre_articulo: str
    proveedor_id: str = ""
    proveedor_nombre: str = ""
    precio_anterior: float = 0.0
    precio_nuevo: float = 0.0
    unidad: str = ""
    diferencia: float = 0.0
    variacion_porcentaje: float = 0.0
    numero_factura: str = ""
    fecha_factura: str = ""
    origen_linea: Dict[str, Any] = field(default_factory=dict)
    accion_sugerida: str = "actualizar"  # actualizar | revisar | mantener
    requiere_revision: bool = False
    avisos: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("CAMBPREC")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")
        self.recalcular()

    def recalcular(self):
        self.diferencia = round(float(self.precio_nuevo or 0) - float(self.precio_anterior or 0), 4)
        if self.precio_anterior:
            self.variacion_porcentaje = round((self.diferencia / self.precio_anterior) * 100, 2)

    def to_dict(self) -> Dict[str, Any]:
        self.recalcular()
        return asdict(self)

@dataclass
class InformeActualizacionPrecios:
    total_cambios: int = 0
    actualizables: int = 0
    requieren_revision: int = 0
    sin_precio_anterior: int = 0
    cambios: List[CambioPrecioFactura] = field(default_factory=list)
    avisos_generales: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("INFUPDPREC")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")
        self.recalcular()

    def recalcular(self):
        self.total_cambios = len(self.cambios)
        self.actualizables = sum(1 for c in self.cambios if not c.requiere_revision and c.accion_sugerida == "actualizar")
        self.requieren_revision = sum(1 for c in self.cambios if c.requiere_revision)
        self.sin_precio_anterior = sum(1 for c in self.cambios if not c.precio_anterior)

    def to_dict(self) -> Dict[str, Any]:
        self.recalcular()
        return {
            **asdict(self),
            "cambios": [c.to_dict() for c in self.cambios],
        }
