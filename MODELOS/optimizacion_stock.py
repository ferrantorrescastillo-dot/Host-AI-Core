from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List

@dataclass
class RecomendacionOptimizacionStock:
    clave: str
    nombre: str
    articulo_id: str = ""
    tipo: str = ""
    prioridad: str = "normal"
    accion: str = ""
    cantidad_sugerida: float = 0.0
    unidad: str = ""
    impacto_estimado: float = 0.0
    motivo: str = ""
    datos: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class InformeOptimizacionStock:
    total_recomendaciones: int
    recomendaciones_criticas: int
    recomendaciones_aviso: int
    ahorro_potencial_estimado: float
    acciones: List[Dict[str, Any]]
    resumen: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
