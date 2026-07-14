from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class ComparacionProveedor:
    proveedor_id: str
    proveedor_nombre: str
    total_registros: int
    precio_medio: float
    estabilidad: str
    frecuencia: str
    incidencias: int
    calidad_historica: str
    puntuacion: float
    articulos: List[str] = field(default_factory=list)
    datos: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    creado_en: str = ""
    def __post_init__(self):
        if not self.id: self.id = nuevo_id("COMPPROV")
        if not self.creado_en: self.creado_en = datetime.now().isoformat(timespec="seconds")
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class InformeComparadorProveedores:
    total_proveedores: int = 0
    comparaciones: List[Dict[str, Any]] = field(default_factory=list)
    mejor_proveedor: Dict[str, Any] = field(default_factory=dict)
    resumen: Dict[str, Any] = field(default_factory=dict)
    lectura_host_ai: str = ""
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
