from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid


def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"


@dataclass
class IngredienteIdea:
    nombre: str
    cantidad: float = 0.0
    unidad: str = ""
    disponible: bool = True
    origen: str = "stock"  # stock | compra | sugerido
    articulo_id: str = ""
    familia: str = ""
    notas: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IdeaCulinaria:
    nombre: str
    tipo: str = "plato"  # plato | menu | elaboracion | comida_personal
    objetivo: str = ""
    ingredientes: List[IngredienteIdea] = field(default_factory=list)
    tecnica_principal: str = ""
    estilo: str = ""
    dificultad: str = "media"
    raciones: int = 1
    fases: List[str] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("IDEA")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "ingredientes": [i.to_dict() for i in self.ingredientes],
        }


@dataclass
class AnalisisCulinario:
    consulta: str
    ideas: List[IdeaCulinaria] = field(default_factory=list)
    necesidades_compra: List[Dict[str, Any]] = field(default_factory=list)
    posibles_acciones: List[str] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("ANALCUL")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "ideas": [i.to_dict() for i in self.ideas],
        }
