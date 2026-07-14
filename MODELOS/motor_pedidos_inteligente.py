from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class DecisionPedidoInteligente:
    articulo_id: str
    nombre_articulo: str
    decision: str
    cantidad_recomendada: float = 0.0
    unidad: str = ""
    proveedor_recomendado: str = ""
    prioridad: str = "normal"
    motivo: str = ""
    confianza: str = "media"
    datos: Dict[str, Any] = field(default_factory=dict)
    requiere_aprobacion: bool = True
    id: str = ""
    creado_en: str = ""
    def __post_init__(self):
        if not self.id: self.id = nuevo_id("PEDINT")
        if not self.creado_en: self.creado_en = datetime.now().isoformat(timespec="seconds")
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class InformeMotorPedidosInteligente:
    total_decisiones: int = 0
    comprar: int = 0
    esperar: int = 0
    cambiar_proveedor: int = 0
    no_comprar: int = 0
    decisiones: List[Dict[str, Any]] = field(default_factory=list)
    resumen: Dict[str, Any] = field(default_factory=dict)
    lectura_host_ai: str = ""
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
