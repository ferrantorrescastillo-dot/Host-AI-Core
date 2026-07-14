from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List

@dataclass
class IngredienteEscandallo307:
    nombre: str
    cantidad: float = 0.0
    unidad: str = ""
    precio_unitario: float = 0.0
    merma_pct: float = 0.0
    coste: float = 0.0
    coste_real_con_merma: float = 0.0
    proveedor: str = ""
    alergenos: List[str] = field(default_factory=list)
    incidencias: List[str] = field(default_factory=list)
    datos: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class AnalisisEscandallo307:
    clave: str
    nombre: str
    raciones: float
    precio_venta: float
    coste_ingredientes: float
    coste_real_con_merma: float
    coste_por_racion: float
    precio_venta_por_racion: float
    margen_bruto_total: float
    margen_bruto_por_racion: float
    margen_pct: float
    food_cost_pct: float
    tiempo_activo_min: int
    tiempo_pasivo_min: int
    coste_mano_obra_estimado: float
    coste_oculto_estimado: float
    coste_total_estimado: float
    beneficio_estimado: float
    rentabilidad: str
    ingredientes: List[Dict[str, Any]]
    incidencias: List[str]
    recomendaciones: List[str]
    datos: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class InformeAnalisisEscandallos307:
    version: str
    total_escandallos: int
    coste_total: float
    venta_total: float
    beneficio_total_estimado: float
    margen_medio_pct: float
    food_cost_medio_pct: float
    recetas_con_perdida: int
    recetas_incompletas: int
    ingredientes_sin_precio: int
    escandallos: List[Dict[str, Any]]
    resumen: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class AlertaEscandallo307:
    gravedad: str
    tipo: str
    escandallo: str
    ingrediente: str = ""
    mensaje: str = ""
    accion_recomendada: str = ""
    datos: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class InformeAlertasEscandallos307:
    version: str
    total_alertas: int
    criticas: int
    avisos: int
    informativas: int
    alertas: List[Dict[str, Any]]
    resumen: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)


@dataclass
class SimulacionCostes307:
    version: str
    total_escandallos: int
    total_escenarios: int
    simulaciones: List[Dict[str, Any]]
    resumen: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class PrediccionRentabilidad307:
    version: str
    total_predicciones: int
    predicciones: List[Dict[str, Any]]
    resumen: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)


@dataclass
class OptimizacionCarta307:
    version: str
    total_platos: int
    platos_estrella: int
    platos_a_potenciar: int
    platos_a_revisar: int
    platos_a_retirar: int
    optimizaciones: List[Dict[str, Any]]
    recomendaciones_carta: List[Dict[str, Any]]
    resumen: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)

@dataclass
class CierreEscandallosInteligentes307:
    version: str
    bloque: str
    modulos_validados: List[str]
    total_escandallos: int
    estado_general: str
    metricas: Dict[str, Any]
    incidencias: List[Dict[str, Any]]
    acciones_recomendadas: List[str]
    informe_final: Dict[str, Any]
    lectura_host_ai: str
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
