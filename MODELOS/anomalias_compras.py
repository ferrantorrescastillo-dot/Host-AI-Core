from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List
from datetime import datetime
import uuid


def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"


@dataclass
class AnomaliaCompra:
    tipo: str
    gravedad: str
    mensaje: str
    origen: str = ""
    articulo_id: str = ""
    nombre_articulo: str = ""
    proveedor_id: str = ""
    proveedor_nombre: str = ""
    numero_factura: str = ""
    datos: Dict[str, Any] = field(default_factory=dict)
    accion_recomendada: str = ""
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("ANOCOMP")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InformeAnomaliasCompras:
    total_anomalias: int = 0
    criticas: int = 0
    avisos: int = 0
    informativas: int = 0
    anomalias: List[Dict[str, Any]] = field(default_factory=list)
    resumen_por_tipo: Dict[str, int] = field(default_factory=dict)
    resumen_por_proveedor: Dict[str, int] = field(default_factory=dict)
    lectura_host_ai: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
