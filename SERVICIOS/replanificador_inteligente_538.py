"""Host AI 5.3.8 - Replanificador Inteligente.

Propone un nuevo planning cuando el detector 5.3.7 encuentra incidencias. No
aplica cambios reales: prepara una replanificación segura y pide confirmación.
"""
from __future__ import annotations

from typing import Any, Dict, List

PESO_PRIORIDAD = {
    "resolver_incidencia": 0,
    "compras_urgentes": 1,
    "recursos_y_personal": 2,
    "produccion_critica": 3,
    "planning": 4,
    "costes": 5,
    "seguimiento": 6,
}

MAPA_ACCIONES = {
    "falta_stock": ("compras_urgentes", "Preparar pedido urgente o validar sustitución"),
    "stock_bajo": ("compras_urgentes", "Añadir a pedido sugerido"),
    "proveedor_no_disponible": ("compras_urgentes", "Buscar proveedor alternativo"),
    "recurso_ocupado": ("recursos_y_personal", "Mover tareas dependientes o reservar recurso alternativo"),
    "falta_personal": ("recursos_y_personal", "Pedir refuerzo o reducir carga del día"),
    "tarea_sin_responsable": ("produccion_critica", "Asignar responsable antes de empezar"),
    "retraso": ("produccion_critica", "Adelantar tareas críticas y mover pasivos"),
    "tarea_bloqueada": ("planning", "Resolver bloqueo antes de ejecutar"),
    "conflicto_produccion_evento": ("planning", "Separar producción y servicio por prioridad"),
}


def _crear_tarea_desde_incidencia(incidencia: Dict[str, Any], indice: int) -> Dict[str, Any]:
    tipo = incidencia.get("tipo", "incidencia")
    grupo, accion = MAPA_ACCIONES.get(tipo, ("resolver_incidencia", "Resolver incidencia antes de aplicar cambios"))
    return {
        "codigo": f"REPLAN_{indice:02d}_{tipo.upper()}",
        "nombre": incidencia.get("titulo") or tipo.replace("_", " ").title(),
        "grupo": grupo,
        "origen": "incidencia",
        "nivel": incidencia.get("nivel", "medio"),
        "accion": incidencia.get("accion_recomendada") or accion,
        "detalle": incidencia.get("detalle", ""),
        "requiere_confirmacion": True,
    }


def _tareas_plan_original(planificacion: Dict[str, Any]) -> List[Dict[str, Any]]:
    tareas: List[Dict[str, Any]] = []
    for paso in planificacion.get("plan", []) or []:
        codigo = str(paso.get("codigo") or "")
        if paso.get("bloqueado_por"):
            continue
        grupo = "costes" if codigo == "COSTES_CALCULAR" else "planning"
        if codigo in {"STOCK_REVISAR", "COMPRAS_PREPARAR"}:
            grupo = "compras_urgentes"
        elif codigo in {"RECURSOS_REVISAR", "PLANNING_GENERAR"}:
            grupo = "recursos_y_personal"
        elif codigo == "PRODUCCION_PLAN":
            grupo = "produccion_critica"
        tareas.append({
            "codigo": codigo,
            "nombre": paso.get("nombre") or codigo,
            "grupo": grupo,
            "origen": "plan_original",
            "nivel": "medio",
            "accion": paso.get("accion") or paso.get("motivo") or "Mantener tarea del planning original.",
            "detalle": paso.get("motivo", ""),
            "requiere_confirmacion": bool(paso.get("requiere_confirmacion")),
        })
    return tareas


def _orden_tarea(tarea: Dict[str, Any]) -> tuple:
    nivel = {"critico": 0, "alto": 1, "medio": 2, "bajo": 3}.get(tarea.get("nivel", "medio"), 2)
    return (PESO_PRIORIDAD.get(tarea.get("grupo", "seguimiento"), 9), nivel, tarea.get("codigo", ""))


def replanificar_operativa_inteligente(planificacion: Dict[str, Any], incidencias: Dict[str, Any], contexto: Dict[str, Any] | None = None, aplicar: bool = False) -> Dict[str, Any]:
    """Genera una propuesta de nuevo planning sin aplicar cambios reales."""
    contexto = contexto or {}
    if not planificacion.get("ok"):
        return {
            "ok": False,
            "estado": "no_replanificable",
            "mensaje": "No puedo replanificar porque no hay un planning válido.",
            "nuevo_planning": [],
            "requiere_confirmacion": True,
            "aplicado": False,
        }

    lista_incidencias = list(incidencias.get("incidencias") or []) if isinstance(incidencias, dict) else []
    if not lista_incidencias:
        return {
            "ok": True,
            "estado": "sin_cambios",
            "mensaje": "No hay incidencias que obliguen a replanificar. Mantendría el planning actual.",
            "nuevo_planning": _tareas_plan_original(planificacion),
            "requiere_confirmacion": False,
            "aplicado": False,
        }

    tareas: List[Dict[str, Any]] = []
    for indice, incidencia in enumerate(lista_incidencias, start=1):
        tareas.append(_crear_tarea_desde_incidencia(incidencia, indice))
    tareas.extend(_tareas_plan_original(planificacion))
    nuevo = sorted(tareas, key=_orden_tarea)

    for orden, tarea in enumerate(nuevo, start=1):
        tarea["orden"] = orden

    soluciones = []
    for incidencia in lista_incidencias:
        soluciones.append({
            "incidencia": incidencia.get("titulo"),
            "nivel": incidencia.get("nivel"),
            "solucion": incidencia.get("accion_recomendada"),
        })

    return {
        "ok": True,
        "estado": "replanificacion_propuesta",
        "mensaje": "Nuevo planning propuesto. No se aplica ningún cambio hasta que el jefe de cocina confirme.",
        "nuevo_planning": nuevo,
        "soluciones": soluciones,
        "total_tareas": len(nuevo),
        "requiere_confirmacion": True,
        "aplicado": bool(aplicar and False),
        "confirmacion_necesaria": "Responde 'sí, aplica la replanificación' para convertir esta propuesta en acciones reales cuando exista escritura segura.",
        "contexto": contexto,
    }


def formatear_replanificacion(resultado: Dict[str, Any]) -> str:
    lineas: List[str] = ["HOST AI 5.3.8 - REPLANIFICADOR INTELIGENTE", "-" * 60, resultado.get("mensaje", "")]
    if not resultado.get("ok"):
        return "\n".join(lineas)
    lineas.append("")
    lineas.append("NUEVO PLANNING PROPUESTO")
    for tarea in resultado.get("nuevo_planning", []):
        marca = "CONFIRMAR" if tarea.get("requiere_confirmacion") else "SEGURO"
        lineas.append(f"{tarea.get('orden', '-')}. [{marca}] {tarea.get('nombre')}")
        lineas.append(f"   Acción: {tarea.get('accion')}")
    if resultado.get("requiere_confirmacion"):
        lineas.append("")
        lineas.append("Antes de aplicar cambios reales necesito confirmación explícita.")
    return "\n".join(lineas)


__all__ = ["replanificar_operativa_inteligente", "formatear_replanificacion"]
