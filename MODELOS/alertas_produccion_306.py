from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List

@dataclass
class AlertaProduccion:
    clave: str
    tipo: str
    gravedad: str = "aviso"
    mensaje: str = ""
    accion_recomendada: str = ""
    datos: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class InformeAlertasProduccion:
    version: str
    total_alertas: int
    alertas_criticas: int
    alertas_aviso: int
    alertas_informativas: int
    alertas: List[Dict[str, Any]]
    resumen: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
