from __future__ import annotations

from dataclasses import asdict, dataclass

from SERVICIOS.host_ai_engine.models import (
    AUTONOMIA_CONSULTAR,
    AUTONOMIA_EJECUTAR,
    AUTONOMIA_PROPONER,
    INC_ACCION_NO_AUTORIZADA,
    INC_CAPACIDAD_NO_IMPLEMENTADA,
)


REQUIERE_CONFIRMACION_GLOBAL = {
    "crear_producto_autorizado",
    "crear_proveedor_autorizado",
    "modificar_precio",
    "archivar_producto",
    "crear_recetas_autorizadas",
    "modificar_receta",
    "confirmar_escandallo",
    "recalcular_escandallo_persistente",
    "crear_menu_autorizado",
    "modificar_menu",
    "asignar_menu_evento",
    "modificar_produccion",
    "generar_compra",
    "modificar_stock",
    "operacion_masiva_stock",
    "resolver_incidencia_persistente",
}

ACCIONES_PROHIBIDAS_GLOBAL = {
    "eliminar_historicos",
    "modificar_eventos_historicos",
    "sobrescribir_precios_anteriores",
    "fusionar_productos_por_similitud",
    "recalcular_costes_confirmados",
    "cambiar_proveedor_preferente",
    "modificar_stock_real",
    "cancelar_tareas_operativas",
    "inventar_cantidades",
    "inventar_precios",
    "inventar_unidades",
    "inventar_proveedores",
    "escritura_directa_repositorio",
}


@dataclass
class PolicyDecision:
    permitida: bool
    requiere_confirmacion: bool
    bloqueada: bool
    tipo_incidencia: str
    motivo: str

    def to_dict(self) -> dict:
        return asdict(self)


class HostAIDecisionPolicy:
    def evaluar(self, agent, capability, step) -> PolicyDecision:
        operacion = str(getattr(step, "operacion", "") or "")
        nivel = str(getattr(step, "nivel_autonomia", "") or "")
        if operacion in ACCIONES_PROHIBIDAS_GLOBAL:
            return PolicyDecision(False, False, True, INC_ACCION_NO_AUTORIZADA, f"Acción prohibida globalmente: {operacion}")
        if agent and operacion in set(agent.acciones_prohibidas or []):
            return PolicyDecision(False, False, True, INC_ACCION_NO_AUTORIZADA, f"Acción prohibida para {agent.identificador}: {operacion}")
        if capability and not bool(capability.implementada) and nivel == AUTONOMIA_EJECUTAR:
            return PolicyDecision(False, False, True, INC_CAPACIDAD_NO_IMPLEMENTADA, f"Capacidad no implementada para ejecución real: {operacion}")

        requiere_confirmacion = bool(getattr(step, "requiere_confirmacion", False))
        if operacion in REQUIERE_CONFIRMACION_GLOBAL:
            requiere_confirmacion = True
        if capability and operacion in set(capability.acciones_requieren_confirmacion or []):
            requiere_confirmacion = True
        if agent and operacion in set(agent.acciones_requieren_confirmacion or []):
            requiere_confirmacion = True
        if bool(getattr(step, "persistencia_real", False)):
            requiere_confirmacion = True
        if nivel == AUTONOMIA_EJECUTAR:
            requiere_confirmacion = True

        if nivel not in {AUTONOMIA_CONSULTAR, AUTONOMIA_PROPONER, AUTONOMIA_EJECUTAR}:
            return PolicyDecision(False, False, True, INC_ACCION_NO_AUTORIZADA, f"Nivel de autonomía no soportado: {nivel}")

        return PolicyDecision(True, requiere_confirmacion, False, "", "Operación permitida por política.")


__all__ = ["HostAIDecisionPolicy", "PolicyDecision", "REQUIERE_CONFIRMACION_GLOBAL", "ACCIONES_PROHIBIDAS_GLOBAL"]