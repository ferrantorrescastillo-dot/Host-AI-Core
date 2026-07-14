from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List

@dataclass
class InformeCierreGestionStock:
    version: str
    estado_general: str
    modulos_validados: List[str]
    metricas: Dict[str, Any]
    incidencias: List[Dict[str, Any]] = field(default_factory=list)
    acciones_recomendadas: List[Dict[str, Any]] = field(default_factory=list)
    informe_ejecutivo: str = ''
    lectura_host_ai: str = ''
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
