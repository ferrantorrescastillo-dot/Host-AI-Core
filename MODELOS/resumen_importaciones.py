from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class ResumenEjecutivoImportaciones:
    total_importaciones: int = 0
    aplicadas: int = 0
    bloqueadas: int = 0
    preparadas: int = 0
    errores: int = 0
    total_lineas: int = 0
    total_precios_aplicados: int = 0
    total_stock_aplicado: int = 0
    proveedores: Dict[str, int] = field(default_factory=dict)
    ultimas_importaciones: List[Dict[str, Any]] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)
    recomendaciones: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("RESUMIMP")
        if not self.creado_en:
            self.creado_en = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
