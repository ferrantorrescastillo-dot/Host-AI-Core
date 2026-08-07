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
    propuesta_id: str = ""
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
    origen_tipo: str = ""
    origen_id: str = ""
    origen_version: int = 0
    propuesta_id: str = ""
    confirmado_en: str = ""
    confirmado_por: str = ""
    borrador_origen_id: str = ""
    recepciones: List[Dict[str, Any]] = field(default_factory=list)
    incidencias: List[Dict[str, Any]] = field(default_factory=list)
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
        self.recepciones = [dict(x or {}) for x in list(self.recepciones or [])]
        self.incidencias = [dict(x or {}) for x in list(self.incidencias or [])]
        self.confirmado_en = str(self.confirmado_en or "").strip()
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
                    "propuesta_id": n.get("propuesta_id", ""),
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
            "origen_tipo": self.origen_tipo,
            "origen_id": self.origen_id,
            "origen_version": self.origen_version,
            "propuesta_id": self.propuesta_id,
            "confirmado_en": self.confirmado_en,
            "confirmado_por": self.confirmado_por,
            "borrador_origen_id": self.borrador_origen_id,
            "recepciones": list(self.recepciones),
            "incidencias": list(self.incidencias),
            "historial": list(self.historial),
            "creado_en": self.creado_en,
            "actualizado_en": self.actualizado_en,
            "enviado_en": self.enviado_en,
            "recibido_en": self.recibido_en,
            "total_lineas": self.total_lineas(),
            "importe_estimado": self.importe_estimado(),
        }


@dataclass
class ProveedorCompra:
    nombre: str
    cif: str = ""
    telefono: str = ""
    email: str = ""
    direccion: str = ""
    comercial: str = ""
    observaciones: str = ""
    pedido_minimo_importe: float | None = None
    portes: float | None = None
    portes_gratis_desde: float | None = None
    plazo_entrega_general_dias: int | None = None
    dias_reparto: List[str] = field(default_factory=list)
    observaciones_comerciales: str = ""
    estado: str = "activo"
    productos_habituales: List[str] = field(default_factory=list)
    id: str = ""
    creado_en: str = ""
    actualizado_en: str = ""

    ESTADOS_VALIDOS = {"activo", "inactivo"}

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("PROVCMP")
        if not self.creado_en:
            self.creado_en = ahora()
        if not self.actualizado_en:
            self.actualizado_en = self.creado_en
        self.nombre = str(self.nombre or "").strip()
        self.estado = str(self.estado or "activo").strip().lower()
        if self.estado not in self.ESTADOS_VALIDOS:
            self.estado = "activo"
        self.pedido_minimo_importe = None if self.pedido_minimo_importe in (None, "") else float(self.pedido_minimo_importe)
        self.portes = None if self.portes in (None, "") else float(self.portes)
        self.portes_gratis_desde = None if self.portes_gratis_desde in (None, "") else float(self.portes_gratis_desde)
        self.plazo_entrega_general_dias = None if self.plazo_entrega_general_dias in (None, "") else int(self.plazo_entrega_general_dias)
        self.dias_reparto = [str(x or "").strip() for x in list(self.dias_reparto or []) if str(x or "").strip()]
        self.productos_habituales = [str(x or "").strip() for x in list(self.productos_habituales or []) if str(x or "").strip()]

    @classmethod
    def from_dict(cls, datos: Dict[str, Any]) -> "ProveedorCompra":
        permitidos = set(cls.__dataclass_fields__.keys())
        return cls(**{k: v for k, v in dict(datos or {}).items() if k in permitidos})

    def tocar(self) -> None:
        self.actualizado_en = ahora()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PropuestaCompraInteligente:
    producto: str
    necesario: float
    disponible: float
    comprar: float
    unidad: str
    origen: str
    prioridad: str
    articulo_id: str = ""
    proveedor_sugerido: str = ""
    motivo_proveedor_sugerido: str = ""
    pedido_id: str = ""
    pedido_estado: str = ""
    estado: str = "pendiente"
    id: str = ""
    creado_en: str = ""
    actualizado_en: str = ""

    ESTADOS_VALIDOS = {"pendiente", "confirmada", "cancelada"}

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("PROP")
        if not self.creado_en:
            self.creado_en = ahora()
        if not self.actualizado_en:
            self.actualizado_en = self.creado_en
        self.producto = str(self.producto or "").strip()
        self.unidad = str(self.unidad or "").strip() or "u"
        self.origen = str(self.origen or "").strip() or "Host AI"
        self.prioridad = str(self.prioridad or "normal").strip().capitalize()
        self.pedido_id = str(self.pedido_id or "").strip()
        self.pedido_estado = str(self.pedido_estado or "").strip().lower()
        self.necesario = float(self.necesario or 0)
        self.disponible = float(self.disponible or 0)
        self.comprar = float(self.comprar or 0)
        self.estado = str(self.estado or "pendiente").strip().lower()
        if self.estado not in self.ESTADOS_VALIDOS:
            self.estado = "pendiente"

    @classmethod
    def from_dict(cls, datos: Dict[str, Any]) -> "PropuestaCompraInteligente":
        permitidos = set(cls.__dataclass_fields__.keys())
        return cls(**{k: v for k, v in dict(datos or {}).items() if k in permitidos})

    def tocar(self) -> None:
        self.actualizado_en = ahora()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AsociacionProductoProveedor:
    producto: str
    producto_normalizado: str
    proveedor_id: str
    proveedor_nombre: str
    preferente: bool = False
    frecuencia: int = 0
    ultima_compra: str = ""
    veces_usado: int = 0
    precio_habitual: float | None = None
    unidad_precio: str = ""
    cantidad_minima_producto: float | None = None
    plazo_entrega_dias: int | None = None
    ultima_actualizacion_precio: str = ""
    observaciones: str = ""
    numero_compras: int = 0
    ultima_compra_en: str = ""
    activo: bool = True
    id: str = ""
    creado_en: str = ""
    actualizado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("ASOCPROV")
        if not self.creado_en:
            self.creado_en = ahora()
        if not self.actualizado_en:
            self.actualizado_en = self.creado_en
        self.producto = str(self.producto or "").strip()
        self.producto_normalizado = str(self.producto_normalizado or "").strip()
        self.proveedor_id = str(self.proveedor_id or "").strip()
        self.proveedor_nombre = str(self.proveedor_nombre or "").strip()
        self.preferente = bool(self.preferente)
        self.activo = bool(self.activo)
        self.veces_usado = max(0, int(self.veces_usado or 0))
        self.frecuencia = max(0, int(self.frecuencia or 0))
        self.precio_habitual = None if self.precio_habitual in (None, "") else float(self.precio_habitual)
        self.unidad_precio = str(self.unidad_precio or "").strip()
        self.cantidad_minima_producto = None if self.cantidad_minima_producto in (None, "") else float(self.cantidad_minima_producto)
        self.plazo_entrega_dias = None if self.plazo_entrega_dias in (None, "") else int(self.plazo_entrega_dias)
        self.ultima_actualizacion_precio = str(self.ultima_actualizacion_precio or "").strip()
        self.observaciones = str(self.observaciones or "").strip()
        self.numero_compras = max(0, int(self.numero_compras or 0))
        self.ultima_compra_en = str(self.ultima_compra_en or "").strip()

    @classmethod
    def from_dict(cls, datos: Dict[str, Any]) -> "AsociacionProductoProveedor":
        permitidos = set(cls.__dataclass_fields__.keys())
        return cls(**{k: v for k, v in dict(datos or {}).items() if k in permitidos})

    def tocar(self) -> None:
        self.actualizado_en = ahora()

    def incrementar_uso(self, fecha: str = "") -> None:
        self.veces_usado = max(0, int(self.veces_usado or 0)) + 1
        self.frecuencia = self.veces_usado
        self.ultima_compra = str(fecha or ahora()).strip() or ahora()
        self.numero_compras = max(0, int(self.numero_compras or 0)) + 1
        self.ultima_compra_en = self.ultima_compra
        self.tocar()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CompraRegistrada:
    producto: str
    cantidad: float
    unidad: str
    proveedor: str
    observaciones: str = ""
    origen: str = "Manual"
    origen_tipo: str = "manual"
    prioridad: str = "Normal"
    articulo_id: str = ""
    propuesta_id: str = ""
    estado: str = "registrada"
    id: str = ""
    creado_en: str = ""
    actualizado_en: str = ""

    ESTADOS_VALIDOS = {"registrada", "cancelada"}

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("COMPRA")
        if not self.creado_en:
            self.creado_en = ahora()
        if not self.actualizado_en:
            self.actualizado_en = self.creado_en
        self.producto = str(self.producto or "").strip()
        self.unidad = str(self.unidad or "").strip() or "u"
        self.proveedor = str(self.proveedor or "").strip() or "Sin proveedor"
        self.origen = str(self.origen or "Manual").strip() or "Manual"
        self.origen_tipo = str(self.origen_tipo or "manual").strip().lower() or "manual"
        self.prioridad = str(self.prioridad or "Normal").strip().capitalize()
        self.cantidad = float(self.cantidad or 0)
        self.estado = str(self.estado or "registrada").strip().lower()
        if self.estado not in self.ESTADOS_VALIDOS:
            self.estado = "registrada"

    @classmethod
    def from_dict(cls, datos: Dict[str, Any]) -> "CompraRegistrada":
        permitidos = set(cls.__dataclass_fields__.keys())
        return cls(**{k: v for k, v in dict(datos or {}).items() if k in permitidos})

    def tocar(self) -> None:
        self.actualizado_en = ahora()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IncidenciaCompra:
    pedido_id: str
    recepcion_id: str
    tipo: str
    descripcion: str
    severidad: str = "media"
    linea_id: str = ""
    proveedor: str = ""
    resuelta: bool = False
    solucion: str = ""
    id: str = ""
    creado_en: str = ""
    actualizado_en: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("INC-COMPRA")
        if not self.creado_en:
            self.creado_en = ahora()
        if not self.actualizado_en:
            self.actualizado_en = self.creado_en
        self.pedido_id = str(self.pedido_id or "").strip()
        self.recepcion_id = str(self.recepcion_id or "").strip()
        self.tipo = str(self.tipo or "incidencia").strip().lower()
        self.descripcion = str(self.descripcion or "").strip()
        self.severidad = str(self.severidad or "media").strip().lower()
        self.linea_id = str(self.linea_id or "").strip()
        self.proveedor = str(self.proveedor or "").strip()
        self.resuelta = bool(self.resuelta)
        self.solucion = str(self.solucion or "").strip()

    @classmethod
    def from_dict(cls, datos: Dict[str, Any]) -> "IncidenciaCompra":
        permitidos = set(cls.__dataclass_fields__.keys())
        return cls(**{k: v for k, v in dict(datos or {}).items() if k in permitidos})

    def tocar(self) -> None:
        self.actualizado_en = ahora()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RecepcionCompra:
    pedido_id: str
    proveedor: str
    estado: str = "parcial"
    lineas: List[Dict[str, Any]] = field(default_factory=list)
    incidencias: List[Dict[str, Any]] = field(default_factory=list)
    observaciones: str = ""
    trazabilidad: Dict[str, Any] = field(default_factory=dict)
    stock_aplicado: bool = False
    stock_aplicado_en: str = ""
    id: str = ""
    creado_en: str = ""
    confirmado_en: str = ""
    actualizado_en: str = ""

    ESTADOS_VALIDOS = {"parcial", "completa", "confirmada", "pendiente", "cancelada"}

    def __post_init__(self):
        if not self.id:
            self.id = nuevo_id("REC-COMPRA")
        if not self.creado_en:
            self.creado_en = ahora()
        if not self.actualizado_en:
            self.actualizado_en = self.creado_en
        self.pedido_id = str(self.pedido_id or "").strip()
        self.proveedor = str(self.proveedor or "").strip()
        self.estado = str(self.estado or "parcial").strip().lower()
        if self.estado not in self.ESTADOS_VALIDOS:
            self.estado = "parcial"
        self.lineas = [dict(x or {}) for x in list(self.lineas or [])]
        self.incidencias = [dict(x or {}) for x in list(self.incidencias or [])]
        self.observaciones = str(self.observaciones or "").strip()
        self.trazabilidad = dict(self.trazabilidad or {})
        self.stock_aplicado = bool(self.stock_aplicado)
        self.stock_aplicado_en = str(self.stock_aplicado_en or "").strip()
        self.confirmado_en = str(self.confirmado_en or "").strip()

    @classmethod
    def from_dict(cls, datos: Dict[str, Any]) -> "RecepcionCompra":
        permitidos = set(cls.__dataclass_fields__.keys())
        return cls(**{k: v for k, v in dict(datos or {}).items() if k in permitidos})

    def tocar(self) -> None:
        self.actualizado_en = ahora()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
