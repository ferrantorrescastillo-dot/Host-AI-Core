"""Host AI 5.3.5 - Planificador Inteligente de Ejecución.

Este servicio toma un flujo operativo generado por 5.3.1 y lo convierte en un
plan de ejecución ordenado, seguro y explicado. No modifica datos reales.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

ORDEN_RECOMENDADO = [
    "EVENTO_CREAR",
    "MENU_ASOCIAR",
    "PRODUCCION_PLAN",
    "RECURSOS_REVISAR",
    "STOCK_REVISAR",
    "COMPRAS_PREPARAR",
    "COSTES_CALCULAR",
    "PLANNING_GENERAR",
]

DEPENDENCIAS = {
    "MENU_ASOCIAR": ["EVENTO_CREAR"],
    "PRODUCCION_PLAN": ["EVENTO_CREAR", "MENU_ASOCIAR"],
    "RECURSOS_REVISAR": ["PRODUCCION_PLAN"],
    "STOCK_REVISAR": ["PRODUCCION_PLAN"],
    "COMPRAS_PREPARAR": ["STOCK_REVISAR"],
    "COSTES_CALCULAR": ["MENU_ASOCIAR", "COMPRAS_PREPARAR"],
    "PLANNING_GENERAR": ["PRODUCCION_PLAN", "RECURSOS_REVISAR", "COMPRAS_PREPARAR"],
}

MOTIVOS_ORDEN = {
    "EVENTO_CREAR": "Primero se debe crear o localizar el evento para no trabajar sin referencia.",
    "MENU_ASOCIAR": "El menú condiciona recetas, producción, compras y costes.",
    "PRODUCCION_PLAN": "La producción define elaboraciones, tiempos y necesidades reales.",
    "RECURSOS_REVISAR": "Los recursos se revisan después de saber qué hay que producir.",
    "STOCK_REVISAR": "El stock se revisa contra la producción necesaria, no antes.",
    "COMPRAS_PREPARAR": "Las compras se preparan solo después de conocer faltantes reales.",
    "COSTES_CALCULAR": "El coste se calcula con menú, compras y necesidades ya definidas.",
    "PLANNING_GENERAR": "El planning final se genera cuando producción, recursos y compras están claros.",
}


def _normalizar_pasos(flujo: Dict[str, Any]) -> List[Dict[str, Any]]:
    pasos = flujo.get("pasos", []) if isinstance(flujo, dict) else []
    normalizados: List[Dict[str, Any]] = []
    for i, paso in enumerate(pasos, start=1):
        if not isinstance(paso, dict):
            continue
        codigo = str(paso.get("codigo") or paso.get("id") or "").strip().upper()
        if not codigo:
            continue
        nuevo = dict(paso)
        nuevo["codigo"] = codigo
        nuevo.setdefault("orden_original", paso.get("orden", i))
        nuevo.setdefault("nombre", codigo.replace("_", " ").title())
        nuevo.setdefault("requiere_confirmacion", False)
        nuevo.setdefault("modifica_datos", False)
        normalizados.append(nuevo)
    return normalizados


def _clave_orden(paso: Dict[str, Any]) -> Tuple[int, int]:
    codigo = paso.get("codigo", "")
    if codigo in ORDEN_RECOMENDADO:
        return (ORDEN_RECOMENDADO.index(codigo), int(paso.get("orden_original", 999)))
    return (999, int(paso.get("orden_original", 999)))


def detectar_dependencias_pendientes(pasos: Iterable[Dict[str, Any]]) -> Dict[str, List[str]]:
    codigos = {p.get("codigo") for p in pasos}
    pendientes: Dict[str, List[str]] = {}
    for codigo in codigos:
        faltan = [dep for dep in DEPENDENCIAS.get(codigo, []) if dep not in codigos]
        if faltan:
            pendientes[codigo] = faltan
    return pendientes


def planificar_ejecucion_inteligente(flujo: Dict[str, Any], contexto: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Ordena y explica el flujo operativo sin ejecutar acciones reales."""
    contexto = contexto or {}
    if not flujo.get("ok", False):
        return {
            "ok": False,
            "estado": "no_planificable",
            "mensaje": "No puedo planificar el flujo porque todavía faltan datos mínimos.",
            "faltan": flujo.get("faltan", []),
            "plan": [],
            "bloqueos": flujo.get("faltan", []),
        }

    pasos = _normalizar_pasos(flujo)
    if not pasos:
        return {
            "ok": False,
            "estado": "sin_pasos",
            "mensaje": "El flujo no contiene pasos operativos para planificar.",
            "plan": [],
            "bloqueos": ["sin_pasos"],
        }

    pasos_ordenados = sorted(pasos, key=_clave_orden)
    dependencias_pendientes = detectar_dependencias_pendientes(pasos_ordenados)
    plan: List[Dict[str, Any]] = []

    for orden, paso in enumerate(pasos_ordenados, start=1):
        codigo = paso["codigo"]
        bloqueado_por = dependencias_pendientes.get(codigo, [])
        estado = "bloqueado" if bloqueado_por else "planificado"
        if paso.get("requiere_confirmacion"):
            estado = "requiere_confirmacion" if not bloqueado_por else estado

        plan.append({
            "orden": orden,
            "codigo": codigo,
            "nombre": paso.get("nombre"),
            "modulo": paso.get("modulo", ""),
            "accion": paso.get("accion", ""),
            "estado": estado,
            "bloqueado_por": bloqueado_por,
            "requiere_confirmacion": bool(paso.get("requiere_confirmacion")),
            "modifica_datos": bool(paso.get("modifica_datos")),
            "motivo": MOTIVOS_ORDEN.get(codigo, "Paso operativo incluido en el flujo generado."),
        })

    return {
        "ok": True,
        "estado": "planificado",
        "datos": flujo.get("datos", {}),
        "plan": plan,
        "bloqueos": dependencias_pendientes,
        "total_pasos": len(plan),
        "mensaje": "Plan inteligente generado. No se han modificado datos reales.",
    }


def formatear_plan_inteligente(planificacion: Dict[str, Any]) -> str:
    lineas: List[str] = []
    lineas.append("HOST AI 5.3.5 - PLANIFICADOR INTELIGENTE")
    lineas.append("-" * 60)
    lineas.append(planificacion.get("mensaje", ""))
    lineas.append("")

    if not planificacion.get("ok"):
        for falta in planificacion.get("faltan", []):
            lineas.append(f"- Falta: {falta}")
        return "\n".join(lineas)

    for paso in planificacion.get("plan", []):
        etiqueta = "CONFIRMAR" if paso.get("requiere_confirmacion") else "SEGURO"
        lineas.append(f"{paso['orden']}. {paso['nombre']} [{etiqueta}]")
        lineas.append(f"   Motivo: {paso.get('motivo')}")
        if paso.get("bloqueado_por"):
            lineas.append(f"   Bloqueado por: {', '.join(paso['bloqueado_por'])}")
    return "\n".join(lineas)


__all__ = [
    "planificar_ejecucion_inteligente",
    "detectar_dependencias_pendientes",
    "formatear_plan_inteligente",
]
