from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class ValidacionModuloCompras:
    modulo: str
    version: str
    ok: bool
    total_registros: int = 0
    mensaje: str = ""
    datos: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    creado_en: str = ""
    def __post_init__(self):
        if not self.id: self.id = nuevo_id("VALCOMP")
        if not self.creado_en: self.creado_en = datetime.now().isoformat(timespec="seconds")
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class InformeCierreInteligenciaCompras:
    version: str = "3.0.4.8"
    ok_global: bool = False
    modulos_validados: int = 0
    total_modulos: int = 8
    validaciones: List[Dict[str, Any]] = field(default_factory=list)
    metricas: Dict[str, Any] = field(default_factory=dict)
    informe_final: Dict[str, Any] = field(default_factory=dict)
    acciones_recomendadas: List[str] = field(default_factory=list)
    lectura_host_ai: str = ""
    id: str = ""
    creado_en: str = ""
    def __post_init__(self):
        if not self.id: self.id = nuevo_id("CIERCOMP")
        if not self.creado_en: self.creado_en = datetime.now().isoformat(timespec="seconds")
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
