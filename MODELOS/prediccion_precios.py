from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List
from datetime import datetime
import uuid


def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"


@dataclass
class PrediccionPrecioArticulo:
    articulo_id: str
    nombre_articulo: str
    total_registros: int
    ultimo_precio: float
    media_movil: float
    tendencia: str
    variacion_porcentual: float
    prediccion_siguiente_precio: float
    nivel_confianza: str
    proveedor_id: str = ""
    unidad: str = ""
    historico: List[Dict[str, Any]] = field(default_factory=list)
    datos: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("PREDPREC")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InformePrediccionPrecios:
    total_articulos: int = 0
    predicciones: List[Dict[str, Any]] = field(default_factory=list)
    resumen_tendencias: Dict[str, int] = field(default_factory=dict)
    lectura_host_ai: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
