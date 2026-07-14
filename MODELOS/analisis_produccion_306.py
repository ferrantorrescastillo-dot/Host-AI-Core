from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List

@dataclass
class ItemAnalisisProduccion:
    clave: str
    nombre: str
    tipo: str = "elaboracion"
    cantidad: float = 0.0
    unidad: str = ""
    tiempo_activo_min: int = 0
    tiempo_pasivo_min: int = 0
    tiempo_total_min: int = 0
    dificultad: str = "media"
    prioridad: str = "normal"
    recursos: List[str] = field(default_factory=list)
    dependencias: List[str] = field(default_factory=list)
    trabajadores_recomendados: int = 1
    riesgo: str = "normal"
    datos: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class InformeAnalisisProduccion:
    version: str
    total_elaboraciones: int
    tiempo_activo_total_min: int
    tiempo_pasivo_total_min: int
    tiempo_total_estimado_min: int
    recursos_detectados: List[str]
    prioridades: Dict[str, int]
    riesgos: Dict[str, int]
    items: List[Dict[str, Any]]
    resumen: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
