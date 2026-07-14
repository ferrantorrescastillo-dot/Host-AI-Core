from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List

@dataclass
class EstadoTareaProduccion:
    clave: str
    elaboracion: str
    estado: str
    avance_pct: float
    retraso_min: int
    riesgo: str
    responsable: str
    recurso: str
    observaciones: List[str] = field(default_factory=list)
    datos: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class InformeControlEjecucionProduccion:
    version: str
    total_tareas: int
    completadas: int
    en_curso: int
    pendientes: int
    bloqueadas: int
    retraso_total_min: int
    riesgo_global: str
    tareas: List[Dict[str, Any]]
    alertas: List[Dict[str, Any]]
    resumen: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AccionReplanificacionProduccion:
    clave: str
    elaboracion: str
    accion: str
    motivo: str
    prioridad: str
    impacto_min: int
    responsable_sugerido: str
    recurso: str
    datos: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class InformeReplanificacionProduccion:
    version: str
    total_acciones: int
    acciones_criticas: int
    minutos_recuperables: int
    estado_replanificacion: str
    acciones: List[Dict[str, Any]]
    nuevo_orden: List[Dict[str, Any]]
    resumen: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
