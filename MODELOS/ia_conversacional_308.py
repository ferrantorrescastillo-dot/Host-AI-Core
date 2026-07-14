from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional

@dataclass
class EntidadConversacional308:
    tipo: str
    valor: str
    normalizado: str = ""
    confianza: float = 0.0
    datos: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class AnalisisLenguajeNatural308:
    version: str
    texto_original: str
    texto_normalizado: str
    intencion_detectada: str
    pipeline_sugerido: str
    accion_sugerida: str
    confianza: float
    entidades: List[Dict[str, Any]]
    contexto: Dict[str, Any]
    requiere_aclaracion: bool
    aclaraciones: List[str]
    solicitud_host_ai: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class TurnoConversacional308:
    usuario: str
    intencion: str
    pipeline: str
    accion: str
    respuesta: str
    datos: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class RespuestaConversacional308:
    version: str
    texto_usuario: str
    respuesta: str
    intencion: str
    pipeline: str
    accion: str
    confianza: float
    contexto_actualizado: Dict[str, Any]
    historial: List[Dict[str, Any]]
    resultado_motor: Dict[str, Any]
    requiere_aprobacion: bool
    acciones_recomendadas: List[str]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)


@dataclass
class SeleccionMotor308:
    version: str
    texto_usuario: str
    intencion: str
    pipeline_seleccionado: str
    accion_seleccionada: str
    parametros: Dict[str, Any]
    confianza: float
    alternativas: List[Dict[str, Any]]
    disponible: bool
    requiere_confirmacion: bool
    motivo: str
    solicitud_host_ai: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class RespuestaNatural308:
    version: str
    tipo_respuesta: str
    titulo: str
    resumen: str
    detalle: List[str]
    recomendaciones: List[str]
    advertencias: List[str]
    datos_fuente: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)


@dataclass
class EntradaMemoriaConversacional308:
    clave: str
    valor: Any
    tipo: str = "contexto"
    prioridad: int = 1
    origen: str = "usuario"
    tags: List[str] = field(default_factory=list)
    metadatos: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class MemoriaConversacional308:
    version: str
    total_entradas: int
    entradas: List[Dict[str, Any]]
    contexto_actual: Dict[str, Any]
    referencias_resueltas: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class AccionAutomatizada308:
    version: str
    texto_usuario: str
    accion_detectada: str
    pipeline_destino: str
    accion_pipeline: str
    parametros: Dict[str, Any]
    requiere_confirmacion: bool
    puede_ejecutarse: bool
    ejecutada: bool
    resultado: Dict[str, Any]
    riesgos: List[str]
    pasos: List[str]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)


@dataclass
class ResultadoAsistenteHostAI308:
    version: str
    texto_usuario: str
    respuesta_final: str
    intencion: str
    pipeline_usado: str
    accion_usada: str
    memoria_usada: Dict[str, Any]
    seleccion_motor: Dict[str, Any]
    respuesta_natural: Dict[str, Any]
    automatizacion: Dict[str, Any]
    requiere_confirmacion: bool
    confianza_global: float
    pasos_ejecutados: List[str]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class CierreIAConversacional308:
    version: str
    modulos_validados: List[str]
    total_modulos: int
    ok_global: bool
    incidencias: List[str]
    metricas: Dict[str, Any]
    informe: Dict[str, Any]
    acciones_recomendadas: List[str]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
