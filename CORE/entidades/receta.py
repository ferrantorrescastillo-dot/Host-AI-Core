
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from .ingrediente import Ingrediente


class EstadoRendimiento(str, Enum):
    IMPORTADO = "IMPORTADO"
    SUGERIDO = "SUGERIDO"
    CONFIRMADO = "CONFIRMADO"

    @classmethod
    def desde_valor(cls, value: Any) -> "EstadoRendimiento":
        return value if isinstance(value, cls) else cls(str(value or ""))


@dataclass
class OrigenRendimiento:
    tipo: str
    referencia: Optional[str] = None
    fecha: Optional[str] = None
    actor_id: Optional[str] = None

    @classmethod
    def desde_dict(cls, data: Any) -> Optional["OrigenRendimiento"]:
        if data is None:
            return None
        if not isinstance(data, dict) or not str(data.get("tipo") or "").strip():
            raise ValueError("El origen del rendimiento no es valido.")
        return cls(
            tipo=str(data["tipo"]).strip(),
            referencia=str(data.get("referencia") or "").strip() or None,
            fecha=str(data.get("fecha") or "").strip() or None,
            actor_id=str(data.get("actor_id") or "").strip() or None,
        )


@dataclass
class RendimientoNeto:
    cantidad: float
    unidad: str
    estado: EstadoRendimiento
    origen: Optional[OrigenRendimiento] = None

    @classmethod
    def desde_dict(cls, data: Any) -> Optional["RendimientoNeto"]:
        if data is None:
            return None
        if not isinstance(data, dict):
            raise ValueError("El rendimiento neto no es valido.")
        try:
            cantidad = float(data.get("cantidad"))
            estado = EstadoRendimiento.desde_valor(data.get("estado"))
        except (TypeError, ValueError) as exc:
            raise ValueError("El rendimiento neto no es valido.") from exc
        return cls(
            cantidad=cantidad,
            unidad=str(data.get("unidad") or "").strip(),
            estado=estado,
            origen=OrigenRendimiento.desde_dict(data.get("origen")),
        )


@dataclass
class Receta:
    codigo:str
    nombre:str
    rendimiento:float
    unidad_rendimiento:str
    ingredientes:list[Ingrediente]=field(default_factory=list)
    estado_rendimiento:Optional[EstadoRendimiento]=None
    origen_rendimiento:Optional[OrigenRendimiento]=None
    rendimiento_neto:Optional[RendimientoNeto]=None
