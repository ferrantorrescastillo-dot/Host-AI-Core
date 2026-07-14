"""Host AI 5.3.6 - Priorizador Inteligente de Tareas.

Ordena las tareas del plan operativo según urgencia, impacto y bloqueos. No
modifica datos reales.
"""
from __future__ import annotations

from typing import Any, Dict, List

ALTA = {"EVENTO_CREAR", "MENU_ASOCIAR", "STOCK_REVISAR", "COMPRAS_PREPARAR"}
MEDIA = {"PRODUCCION_PLAN", "RECURSOS_REVISAR", "PLANNING_GENERAR"}
BAJA = {"COSTES_CALCULAR"}

MOTIVOS_PRIORIDAD = {
    "EVENTO_CREAR": "Sin evento no se debe generar producción ni compras.",
    "MENU_ASOCIAR": "El menú define recetas, cantidades y costes.",
    "STOCK_REVISAR": "El stock evita compras innecesarias y descubre roturas.",
    "COMPRAS_PREPARAR": "Las compras deben prepararse pronto para evitar falta de género.",
    "PRODUCCION_PLAN": "Producción necesita planificación, pero depende de evento y menú.",
    "RECURSOS_REVISAR": "Los recursos se revisan después del plan de producción.",
    "PLANNING_GENERAR": "El planning se genera cuando ya están claras las tareas.",
    "COSTES_CALCULAR": "Rentabilidad es clave, pero no bloquea la operativa inmediata.",
}


def _prioridad_para_paso(paso: Dict[str, Any]) -> str:
    codigo = paso.get("codigo")
    if paso.get("bloqueado_por"):
        return "alta"
    if codigo in ALTA:
        return "alta"
    if codigo in MEDIA:
        return "media"
    if codigo in BAJA:
        return "baja"
    if paso.get("requiere_confirmacion") or paso.get("modifica_datos"):
        return "alta"
    return "media"


def priorizar_tareas_operativas(planificacion: Dict[str, Any]) -> Dict[str, Any]:
    """Clasifica pasos planificados en prioridad alta, media y baja."""
    if not planificacion.get("ok"):
        return {
            "ok": False,
            "estado": "no_priorizable",
            "mensaje": "No puedo priorizar tareas porque no hay un plan operativo válido.",
            "prioridades": {"alta": [], "media": [], "baja": []},
        }

    prioridades = {"alta": [], "media": [], "baja": []}
    for paso in planificacion.get("plan", []):
        prioridad = _prioridad_para_paso(paso)
        item = {
            "codigo": paso.get("codigo"),
            "nombre": paso.get("nombre"),
            "orden_plan": paso.get("orden"),
            "estado": paso.get("estado"),
            "requiere_confirmacion": bool(paso.get("requiere_confirmacion")),
            "motivo": MOTIVOS_PRIORIDAD.get(paso.get("codigo"), "Tarea necesaria dentro del flujo operativo."),
        }
        if paso.get("bloqueado_por"):
            item["motivo"] = "Debe resolverse pronto porque bloquea o depende de otros pasos."
            item["bloqueado_por"] = paso.get("bloqueado_por")
        prioridades[prioridad].append(item)

    total = sum(len(v) for v in prioridades.values())
    return {
        "ok": True,
        "estado": "priorizado",
        "prioridades": prioridades,
        "total_tareas": total,
        "mensaje": "Tareas priorizadas como lo haría un jefe de cocina: primero lo que bloquea servicio, producción o compras.",
    }


def formatear_prioridades(resultado: Dict[str, Any]) -> str:
    lineas: List[str] = []
    lineas.append("HOST AI 5.3.6 - PRIORIZADOR DE TAREAS")
    lineas.append("-" * 60)
    lineas.append(resultado.get("mensaje", ""))

    if not resultado.get("ok"):
        return "\n".join(lineas)

    titulos = {"alta": "PRIORIDAD ALTA", "media": "PRIORIDAD MEDIA", "baja": "PRIORIDAD BAJA"}
    for clave in ["alta", "media", "baja"]:
        lineas.append("")
        lineas.append(titulos[clave])
        tareas = resultado.get("prioridades", {}).get(clave, [])
        if not tareas:
            lineas.append("- Sin tareas")
            continue
        for tarea in tareas:
            lineas.append(f"- {tarea.get('nombre')} ({tarea.get('codigo')})")
            lineas.append(f"  Motivo: {tarea.get('motivo')}")
    return "\n".join(lineas)


__all__ = ["priorizar_tareas_operativas", "formatear_prioridades"]
