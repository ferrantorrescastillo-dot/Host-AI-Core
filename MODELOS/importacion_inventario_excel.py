from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class LineaInventarioExcel:
    nombre: str
    cantidad: float
    unidad: str
    articulo_id: str = ""
    familia: str = ""
    ubicacion: str = ""
    caducidad: str = ""
    lote: str = ""
    proveedor: str = ""
    precio_unitario: float = 0.0
    origen: str = "excel"
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("LININV")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class CambioInventarioExcel:
    articulo_id: str
    nombre: str
    anterior: float
    nuevo: float
    diferencia: float
    unidad: str
    accion: str = "actualizar"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ErrorImportacionInventario:
    hoja: str
    fila: int
    mensaje: str
    datos: Dict[str, Any] = field(default_factory=dict)
    nivel: str = "error"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ResultadoImportacionInventario:
    archivo: str
    modo: str = "vista_previa"
    lineas_detectadas: int = 0
    lineas_importadas: int = 0
    articulos_creados: int = 0
    stock_actualizado: int = 0
    cambios: List[CambioInventarioExcel] = field(default_factory=list)
    lineas: List[Dict[str, Any]] = field(default_factory=list)
    errores: List[ErrorImportacionInventario] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("IMPINV")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "cambios": [c.to_dict() for c in self.cambios],
            "errores": [e.to_dict() for e in self.errores],
        }
