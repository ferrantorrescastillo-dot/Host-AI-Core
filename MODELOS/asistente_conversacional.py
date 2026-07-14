from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid


def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"


@dataclass
class IntencionConversacional:
    texto: str
    intencion: str
    confianza: float = 0.0
    parametros: Dict[str, Any] = field(default_factory=dict)
    pipeline: str = ""
    accion: str = ""
    avisos: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("INTCONV")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RespuestaConversacional:
    texto_usuario: str
    respuesta: str
    intencion: Dict[str, Any]
    resultado: Dict[str, Any] = field(default_factory=dict)
    acciones_recomendadas: List[str] = field(default_factory=list)
    requiere_aprobacion: bool = False
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("RESPCONV")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
