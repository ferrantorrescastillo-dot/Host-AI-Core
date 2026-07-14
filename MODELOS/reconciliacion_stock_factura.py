from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class ResultadoReconciliacionStock:
    articulo_id: str
    nombre_articulo: str
    cantidad_factura: float = 0.0
    cantidad_aplicada: float = 0.0
    unidad: str = ""
    diferencia: float = 0.0
    estado: str = "pendiente"  # correcto | diferencia | pendiente
    avisos: List[str] = field(default_factory=list)
    datos: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("RECSTOCK")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class InformeReconciliacionStock:
    resultados: List[ResultadoReconciliacionStock] = field(default_factory=list)
    total: int = 0
    correctos: int = 0
    con_diferencias: int = 0
    pendientes: int = 0
    puede_cerrar_factura: bool = False
    avisos_generales: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("INFRECSTOCK")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")
        self.recalcular()

    def recalcular(self):
        self.total = len(self.resultados)
        self.correctos = sum(1 for r in self.resultados if r.estado == "correcto")
        self.con_diferencias = sum(1 for r in self.resultados if r.estado == "diferencia")
        self.pendientes = sum(1 for r in self.resultados if r.estado == "pendiente")
        self.puede_cerrar_factura = self.total > 0 and self.con_diferencias == 0 and self.pendientes == 0

    def to_dict(self) -> Dict[str, Any]:
        self.recalcular()
        return {
            **asdict(self),
            "resultados": [r.to_dict() for r in self.resultados],
        }
