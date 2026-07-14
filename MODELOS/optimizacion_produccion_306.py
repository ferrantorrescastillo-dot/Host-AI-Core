from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List

@dataclass
class OportunidadOptimizacionProduccion:
    clave: str
    elaboracion: str
    tipo: str
    prioridad: str
    ahorro_min_estimado: int
    recurso: str
    responsable_sugerido: str
    descripcion: str
    acciones: List[str] = field(default_factory=list)
    datos: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class InformeOptimizacionProduccion:
    version: str
    total_oportunidades: int
    oportunidades_criticas: int
    ahorro_total_min_estimado: int
    estado_optimizacion: str
    oportunidades: List[Dict[str, Any]]
    plan_optimizado: List[Dict[str, Any]]
    recursos_optimizados: Dict[str, Any]
    resumen: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ComprobacionCierreProduccion:
    clave: str
    modulo: str
    estado: str
    mensaje: str
    gravedad: str
    datos: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class InformeCierreProduccion:
    version: str
    estado_cierre: str
    modulos_validados: int
    comprobaciones_totales: int
    comprobaciones_ok: int
    comprobaciones_aviso: int
    comprobaciones_criticas: int
    metricas: Dict[str, Any]
    comprobaciones: List[Dict[str, Any]]
    informe_final: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
