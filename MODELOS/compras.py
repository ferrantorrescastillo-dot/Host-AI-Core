from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid


def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"


def ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class NecesidadCompra:
    nombre: str
    cantidad: float
    unidad: str
    familia: str = ""
    proveedor_preferente: str = ""
    motivo: str = ""
    prioridad: int = 50
    articulo_id: str = ""
    fecha_necesaria: str = ""
    estado: str = "pendiente"
    id: str = ""
    creado_en: str = ""
    actualizado_en: str = ""

    ESTADOS_VALIDOS = {"pendiente", "comprada", "cancelada"}

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("NEC")
        if not self.creado_en:
            self.creado_en = ahora()
        if not self.actualizado_en:
            self.actualizado_en = self.creado_en
        self.estado = (self.estado or "pendiente").strip().lower()
        if self.estado not in self.ESTADOS_VALIDOS:
            self.estado = "pendiente"
        self.cantidad = float(self.cantidad)
        self.prioridad = int(self.prioridad)

    @classmethod
    def from_dict(cls, datos: Dict[str, Any]) -> "NecesidadCompra":
        permitidos = set(cls.__dataclass_fields__.keys())
        return cls(**{k: v for k, v in dict(datos or {}).items() if k in permitidos})

    def tocar(self) -> None:
        self.actualizado_en = ahora()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LineaPedido:
    nombre: str
    cantidad: float
    unidad: str
    articulo_id: str = ""
    familia: str = ""
    necesidad_id: str = ""
    precio_unitario: float = 0.0
    observaciones: str = ""
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("LIN")
        self.cantidad = float(self.cantidad)
        self.precio_unitario = float(self.precio_unitario or 0)

    @classmethod
    def from_dict(cls, datos: Dict[str, Any]) -> "LineaPedido":
        permitidos = set(cls.__dataclass_fields__.keys())
        return cls(**{k: v for k, v in dict(datos or {}).items() if k in permitidos})

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PedidoSugerido:
    proveedor: str
    lineas: List[LineaPedido] = field(default_factory=list)
    estado: str = "borrador"
    observaciones: str = ""
    historial: List[Dict[str, str]] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""
    actualizado_en: str = ""
    enviado_en: str = ""
    recibido_en: str = ""

    ESTADOS_VALIDOS = {"borrador", "preparado", "enviado", "recibido", "cancelado"}

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("PED")
        if not self.creado_en:
            self.creado_en = ahora()
        if not self.actualizado_en:
            self.actualizado_en = self.creado_en
        self.estado = (self.estado or "borrador").strip().lower()
        if self.estado not in self.ESTADOS_VALIDOS:
            self.estado = "borrador"
        self.lineas = [l if isinstance(l, LineaPedido) else LineaPedido.from_dict(l) for l in self.lineas]
        if not self.historial:
            self.historial = [{"fecha": self.creado_en, "accion": "creado", "detalle": "Pedido creado en borrador."}]

    @classmethod
    def from_dict(cls, datos: Dict[str, Any]) -> "PedidoSugerido":
        datos = dict(datos or {})
        # Compatibilidad con C1: los pedidos antiguos guardaban `necesidades`.
        lineas_raw = datos.pop("lineas", None)
        if lineas_raw is None:
            lineas_raw = []
            for n in datos.pop("necesidades", []) or []:
                lineas_raw.append({
                    "nombre": n.get("nombre", ""),
                    "cantidad": n.get("cantidad", 0),
                    "unidad": n.get("unidad", ""),
                    "articulo_id": n.get("articulo_id", ""),
                    "familia": n.get("familia", ""),
                    "necesidad_id": n.get("id", ""),
                })
        datos.pop("total_lineas", None)
        datos.pop("importe_estimado", None)
        permitidos = set(cls.__dataclass_fields__.keys()) - {"lineas"}
        return cls(lineas=[LineaPedido.from_dict(l) for l in lineas_raw], **{k: v for k, v in datos.items() if k in permitidos})

    def tocar(self, accion: str = "actualizado", detalle: str = "") -> None:
        self.actualizado_en = ahora()
        self.historial.append({"fecha": self.actualizado_en, "accion": accion, "detalle": detalle})

    def total_lineas(self) -> int:
        return len(self.lineas)

    def importe_estimado(self) -> float:
        return round(sum(l.cantidad * l.precio_unitario for l in self.lineas), 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "proveedor": self.proveedor,
            "lineas": [l.to_dict() for l in self.lineas],
            "estado": self.estado,
            "observaciones": self.observaciones,
            "historial": list(self.historial),
            "creado_en": self.creado_en,
            "actualizado_en": self.actualizado_en,
            "enviado_en": self.enviado_en,
            "recibido_en": self.recibido_en,
            "total_lineas": self.total_lineas(),
            "importe_estimado": self.importe_estimado(),
        }
