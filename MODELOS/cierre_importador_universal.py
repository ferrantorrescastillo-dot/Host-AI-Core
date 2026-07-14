from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class InformeCierreImportadorUniversal:
    version: str = "3.0.3.8.5"
    listo_para_uso: bool = False
    modulos_comprobados: List[str] = field(default_factory=list)
    modulos_faltantes: List[str] = field(default_factory=list)
    pruebas_recomendadas: List[str] = field(default_factory=list)
    flujo_completo: List[str] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)
    recomendaciones: List[str] = field(default_factory=list)
    resumen: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("CIERREIMP")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
