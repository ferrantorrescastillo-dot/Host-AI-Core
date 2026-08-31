from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
import uuid


ESTADO_ENGINE_OK = "OK"
ESTADO_ENGINE_OK_SIMULADO = "OK_SIMULADO"
ESTADO_ENGINE_ERROR = "ERROR"

AUTONOMIA_CONSULTAR = "CONSULTAR"
AUTONOMIA_PROPONER = "PROPONER"
AUTONOMIA_EJECUTAR = "EJECUTAR"

ESTADO_SOLICITUD_RECIBIDA = "RECIBIDA"
ESTADO_SOLICITUD_CLASIFICADA = "CLASIFICADA"
ESTADO_SOLICITUD_PLANIFICADA = "PLANIFICADA"
ESTADO_SOLICITUD_ESPERANDO_CONFIRMACION = "ESPERANDO_CONFIRMACION"
ESTADO_SOLICITUD_EN_EJECUCION = "EN_EJECUCION"
ESTADO_SOLICITUD_COMPLETADA = "COMPLETADA"
ESTADO_SOLICITUD_COMPLETADA_CON_INCIDENCIAS = "COMPLETADA_CON_INCIDENCIAS"
ESTADO_SOLICITUD_CANCELADA = "CANCELADA"
ESTADO_SOLICITUD_BLOQUEADA = "BLOQUEADA"
ESTADO_SOLICITUD_ERROR = "ERROR"

ESTADO_PASO_PENDIENTE = "PENDIENTE"
ESTADO_PASO_PREPARADO = "PREPARADO"
ESTADO_PASO_EJECUTADO = "EJECUTADO"
ESTADO_PASO_OMITIDO = "OMITIDO"
ESTADO_PASO_BLOQUEADO = "BLOQUEADO"
ESTADO_PASO_ERROR = "ERROR"

ESTADO_CONFIRMACION_PENDIENTE = "PENDIENTE"
ESTADO_CONFIRMACION_ACEPTADA = "ACEPTADA"
ESTADO_CONFIRMACION_RECHAZADA = "RECHAZADA"
ESTADO_CONFIRMACION_PARCIAL = "PARCIAL"
ESTADO_CONFIRMACION_CADUCADA = "CADUCADA"
ESTADO_CONFIRMACION_CANCELADA = "CANCELADA"

INC_DATO_OBLIGATORIO_AUSENTE = "DATO_OBLIGATORIO_AUSENTE"
INC_DATO_SECUNDARIO_AUSENTE = "DATO_SECUNDARIO_AUSENTE"
INC_DATO_AMBIGUO = "DATO_AMBIGUO"
INC_CONFLICTO_FUENTES = "CONFLICTO_ENTRE_FUENTES"
INC_ACCION_NO_AUTORIZADA = "ACCION_NO_AUTORIZADA"
INC_SERVICIO_NO_DISPONIBLE = "SERVICIO_NO_DISPONIBLE"
INC_CAPACIDAD_NO_IMPLEMENTADA = "CAPACIDAD_NO_IMPLEMENTADA"


def _serialize_value(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, list):
        return [_serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    return value


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


@dataclass
class HostAIEngineRequest:
    origen: str
    modulo: str
    tipo_peticion: str
    datos_enviados: dict[str, Any]
    proveedor_preferido: str = "SIMULADO"
    formato_entrada: str = "texto"
    request_id: str = field(default_factory=lambda: f"HAE-{uuid.uuid4()}")
    operation_id: str = ""
    session_id: str = ""
    entity_type: str = ""
    entity_id: str = ""
    creado_en: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HostAIEngineResponse:
    request_id: str
    origen: str
    modulo: str
    tipo_peticion: str
    respuesta: dict[str, Any]
    estado: str
    errores: list[str]
    tiempo_ms: int
    proveedor: str
    modelo: str
    usage: dict[str, Any] = field(default_factory=dict)
    cost_breakdown: dict[str, Any] = field(default_factory=dict)
    finalizado_en: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HostAIProviderResult:
    ok: bool
    proveedor: str
    modelo: str
    salida: dict[str, Any]
    errores: list[str] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)
    response_id: str = ""
    service_tier: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentCapabilityContract:
    identificador: str
    nombre: str
    descripcion: str
    modulo_objetivo: str
    servicio_objetivo: str
    tipos_peticion_soportados: list[str]
    acciones_permitidas: list[str]
    acciones_requieren_confirmacion: list[str]
    acciones_prohibidas: list[str]
    nivel_minimo: str
    prioridad: int
    activa: bool = True
    version_contrato: str = "1.0"
    implementada: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentContract:
    identificador: str
    nombre: str
    descripcion: str
    modulos_que_puede_consultar: list[str]
    servicios_que_puede_invocar: list[str]
    tipos_peticion_soportados: list[str]
    acciones_permitidas: list[str]
    acciones_requieren_confirmacion: list[str]
    acciones_prohibidas: list[str]
    prioridad: int
    activo: bool
    version_contrato: str
    capacidades: list[AgentCapabilityContract] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "capacidades": [_serialize_value(c) for c in self.capacidades],
        }


@dataclass
class PlanStep:
    orden: int
    agente: str
    operacion: str
    nivel_autonomia: str
    entradas: dict[str, Any]
    dependencias: list[int] = field(default_factory=list)
    resultado_esperado: str = ""
    requiere_confirmacion: bool = False
    estado: str = ESTADO_PASO_PENDIENTE
    resultado_real: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    compensacion_o_reversion_posible: str = ""
    capacidad_identificador: str = ""
    persistencia_real: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConfirmationRequest:
    id_confirmacion: str
    id_solicitud: str
    acciones_incluidas: list[dict[str, Any]]
    resumen_visible: str
    impacto: str
    riesgos: list[str]
    fecha_solicitud: str
    estado: str = ESTADO_CONFIRMACION_PENDIENTE
    usuario_que_responde: str = ""
    fecha_respuesta: str = ""
    alcance_autorizado: dict[str, Any] = field(default_factory=dict)
    caducidad_opcional: str = ""
    plan_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionAuditEntry:
    fecha: str
    tipo: str
    detalle: str
    datos: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HostAISolicitudOperativa:
    usuario: str
    origen: str
    modulo_origen: str
    texto_original: str
    intencion: str
    nivel_de_autonomia: str
    datos_de_entrada: dict[str, Any]
    proveedor_preferido: str = "SIMULADO"
    formato_entrada: str = "texto"
    contexto: dict[str, Any] = field(default_factory=dict)
    agente_principal: str = ""
    agentes_delegados: list[str] = field(default_factory=list)
    plan: dict[str, Any] = field(default_factory=dict)
    pasos: list[PlanStep] = field(default_factory=list)
    acciones_propuestas: list[dict[str, Any]] = field(default_factory=list)
    confirmaciones_requeridas: list[ConfirmationRequest] = field(default_factory=list)
    confirmaciones_recibidas: list[ConfirmationRequest] = field(default_factory=list)
    resultado: dict[str, Any] = field(default_factory=dict)
    incidencias: list[dict[str, Any]] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)
    estado: str = ESTADO_SOLICITUD_RECIBIDA
    duracion_ms: int = 0
    version_del_contrato: str = "1.0"
    id_solicitud: str = field(default_factory=lambda: _new_id("HAS"))
    fecha: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    id_correlacion: str = field(default_factory=lambda: _new_id("CORR"))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["pasos"] = [_serialize_value(p) for p in self.pasos]
        data["confirmaciones_requeridas"] = [_serialize_value(c) for c in self.confirmaciones_requeridas]
        data["confirmaciones_recibidas"] = [_serialize_value(c) for c in self.confirmaciones_recibidas]
        return data


CAPACIDADES_FUTURAS_ENGINE = {
    "interpretar_texto": "preparada",
    "interpretar_word": "preparada",
    "interpretar_excel": "preparada",
    "interpretar_pdf": "preparada",
    "interpretar_imagenes": "preparada",
    "interpretar_conversaciones": "preparada",
    "responder_preguntas": "preparada",
    "generar_recetas": "preparada",
    "generar_escandallos": "preparada",
    "resolver_incidencias": "preparada",
    "proponer_proveedores": "preparada",
    "detectar_duplicados": "preparada",
    "calcular_rentabilidades": "preparada",
    "sugerir_menus": "preparada",
    "generar_produccion": "preparada",
    "lenguaje_natural": "preparada",
}
