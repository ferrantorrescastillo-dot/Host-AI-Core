from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class ArticuloImportadoExcel:
    nombre: str
    articulo_id: str
    unidad: str = ""
    familia: str = ""
    proveedor: str = ""
    precio_unitario: float = 0.0
    stock_minimo: float = 0.0
    ubicacion: str = ""
    codigo: str = ""
    alergenos: str = ""
    origen: str = "excel"
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = self.articulo_id or nuevo_id("ART")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ErrorImportacionArticulo:
    hoja: str
    fila: int
    mensaje: str
    datos: Dict[str, Any] = field(default_factory=dict)
    nivel: str = "error"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ResultadoImportacionArticulos:
    archivo: str
    modo: str = "vista_previa"
    articulos_detectados: int = 0
    articulos_importados: int = 0
    articulos_actualizados: int = 0
    precios_registrados: int = 0
    duplicados_detectados: int = 0
    errores: List[ErrorImportacionArticulo] = field(default_factory=list)
    articulos: List[Dict[str, Any]] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("IMPART")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "errores": [e.to_dict() for e in self.errores],
        }
