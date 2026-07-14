from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid


def ahora_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def nuevo_id(prefijo: str) -> str:
    return f'{prefijo}-{uuid.uuid4().hex[:12].upper()}'


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class TipoEntidad(StrEnum):
    RECETA = 'RECETA'
    ARTICULO = 'ARTICULO'
    PROVEEDOR = 'PROVEEDOR'
    UNIDAD = 'UNIDAD'
    FAMILIA = 'FAMILIA'
    ELABORACION = 'ELABORACION'
    RELACION = 'RELACION'
    GENERICA = 'GENERICA'


class TipoConflicto(StrEnum):
    ENTIDAD_NO_EXISTE = 'ENTIDAD_NO_EXISTE'
    ENTIDAD_AMBIGUA = 'ENTIDAD_AMBIGUA'
    ENTIDAD_INCOMPLETA = 'ENTIDAD_INCOMPLETA'
    ARTICULO_SIN_PRECIO = 'ARTICULO_SIN_PRECIO'
    UNIDAD_DESCONOCIDA = 'UNIDAD_DESCONOCIDA'
    RELACION_NO_RESUELTA = 'RELACION_NO_RESUELTA'
    DUPLICADO_PROBABLE = 'DUPLICADO_PROBABLE'
    DATO_INCONSISTENTE = 'DATO_INCONSISTENTE'
    POLITICA_REQUERIDA = 'POLITICA_REQUERIDA'
    GENERICO = 'GENERICO'


class SeveridadConflicto(StrEnum):
    INFO = 'INFO'
    AVISO = 'AVISO'
    BLOQUEANTE = 'BLOQUEANTE'
    CRITICA = 'CRITICA'


class EstadoConflicto(StrEnum):
    DETECTADO = 'DETECTADO'
    CLASIFICADO = 'CLASIFICADO'
    EN_RESOLUCION = 'EN_RESOLUCION'
    PENDIENTE = 'PENDIENTE'
    RESUELTO = 'RESUELTO'
    APLICADO = 'APLICADO'
    CERRADO = 'CERRADO'
    FALLIDO = 'FALLIDO'
    CANCELADO = 'CANCELADO'
    REABIERTO = 'REABIERTO'


class AccionResolucion(StrEnum):
    VINCULAR = 'VINCULAR'
    CREAR = 'CREAR'
    EDITAR = 'EDITAR'
    NORMALIZAR = 'NORMALIZAR'
    MANTENER_PENDIENTE = 'MANTENER_PENDIENTE'
    CANCELAR = 'CANCELAR'
    SIMULAR = 'SIMULAR'


@dataclass(slots=True)
class ConflictoMUR:
    organizacion_id: str
    flujo_id: str
    origen_modulo: str
    tipo_entidad: TipoEntidad
    tipo_conflicto: TipoConflicto
    severidad: SeveridadConflicto
    dato_original: str
    dato_normalizado: str = ''
    rol_contextual: str = ''
    contexto: dict[str, Any] = field(default_factory=dict)
    candidatos: list[dict[str, Any]] = field(default_factory=list)
    acciones_permitidas: list[str] = field(default_factory=list)
    checkpoint_id: str = ''
    politica_aplicada: str = ''
    conflicto_id: str = field(default_factory=lambda: nuevo_id('MUR'))
    estado: EstadoConflicto = EstadoConflicto.DETECTADO
    version: int = 1
    creado_en: str = field(default_factory=ahora_utc)
    actualizado_en: str = field(default_factory=ahora_utc)
    motivo_estado: str = ''
    resolutor_id: str = ''

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ('tipo_entidad', 'tipo_conflicto', 'severidad', 'estado'):
            data[key] = str(data[key])
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ConflictoMUR':
        d = dict(data)
        d['tipo_entidad'] = TipoEntidad(d.get('tipo_entidad', 'GENERICA'))
        d['tipo_conflicto'] = TipoConflicto(d.get('tipo_conflicto', 'GENERICO'))
        d['severidad'] = SeveridadConflicto(d.get('severidad', 'AVISO'))
        d['estado'] = EstadoConflicto(d.get('estado', 'DETECTADO'))
        return cls(**d)


@dataclass(slots=True)
class CheckpointMUR:
    flujo_id: str
    modulo: str
    operacion: str
    paso: str
    estado_parcial: dict[str, Any]
    huella_entrada: str = ''
    version_flujo: int = 1
    dependencias: list[str] = field(default_factory=list)
    checkpoint_id: str = field(default_factory=lambda: nuevo_id('CHK'))
    creado_en: str = field(default_factory=ahora_utc)
    actualizado_en: str = field(default_factory=ahora_utc)
    activo: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'CheckpointMUR':
        return cls(**dict(data))


@dataclass(slots=True)
class SesionResolucionMUR:
    conflicto_id: str
    usuario_id: str
    resolutor_id: str
    acciones_disponibles: list[str]
    sesion_id: str = field(default_factory=lambda: nuevo_id('SES'))
    estado: str = 'ABIERTA'
    payload: dict[str, Any] = field(default_factory=dict)
    creada_en: str = field(default_factory=ahora_utc)
    actualizada_en: str = field(default_factory=ahora_utc)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'SesionResolucionMUR':
        return cls(**dict(data))


@dataclass(slots=True)
class ResultadoResolucion:
    ok: bool
    accion: str
    mensaje: str
    datos: dict[str, Any] = field(default_factory=dict)
    requiere_recalculo: bool = True
    aprendizaje_sugerido: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EventoAuditoriaMUR:
    conflicto_id: str
    evento: str
    actor: str
    detalle: dict[str, Any] = field(default_factory=dict)
    evento_id: str = field(default_factory=lambda: nuevo_id('AUD'))
    creado_en: str = field(default_factory=ahora_utc)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'EventoAuditoriaMUR':
        return cls(**dict(data))
