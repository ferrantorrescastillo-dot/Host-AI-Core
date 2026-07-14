from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List

@dataclass
class NecesidadStockPredicha:
    clave: str
    nombre: str
    articulo_id: str = ""
    unidad: str = ""
    stock_actual: float = 0.0
    consumo_diario_estimado: float = 0.0
    dias_cobertura: float = 0.0
    necesidad_periodo: float = 0.0
    cantidad_a_reponer: float = 0.0
    fecha_rotura_estimada: str = ""
    prioridad: str = "normal"
    confianza: float = 0.0
    motivos: List[str] = field(default_factory=list)
    datos: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class InformePrediccionNecesidadesStock:
    total_articulos: int
    total_necesidades: int
    total_criticas: int
    total_avisos: int
    valor_estimado_reposicion: float
    horizonte_dias: int
    items: List[Dict[str, Any]]
    resumen: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
