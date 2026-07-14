from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List

@dataclass
class BloquePlanProduccion:
    clave: str
    nombre: str
    dia: int
    inicio_min: int
    fin_min: int
    duracion_min: int
    tipo_tiempo: str
    recurso: str
    prioridad: str
    dependencias: List[str] = field(default_factory=list)
    datos: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class InformePlanificacionProduccion:
    version: str
    total_elaboraciones: int
    total_bloques: int
    dias_necesarios: int
    minutos_activos: int
    minutos_pasivos: int
    ocupacion_pct: float
    estado_plan: str
    bloques: List[Dict[str, Any]]
    resumen: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AsignacionCocineroProduccion:
    cocinero: str
    dia: int
    inicio_min: int
    fin_min: int
    duracion_min: int
    clave: str
    elaboracion: str
    tarea: str
    recurso: str
    prioridad: str
    riesgo: str
    datos: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class InformeAsignacionProduccion:
    version: str
    total_asignaciones: int
    cocineros: int
    dias_necesarios: int
    carga_por_cocinero: Dict[str, int]
    conflictos: List[Dict[str, Any]]
    estado_asignacion: str
    asignaciones: List[Dict[str, Any]]
    resumen: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
