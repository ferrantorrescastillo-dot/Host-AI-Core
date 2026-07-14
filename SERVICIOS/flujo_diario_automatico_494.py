from __future__ import annotations

from typing import Dict, Any, Iterable, List

from SERVICIOS.motor_decisiones_operativas_491 import generar_decisiones_operativas
from SERVICIOS.respuestas_jefe_cocina_493 import explicar_decisiones_como_jefe


def generar_flujo_diario(datos: Dict[str, Any]) -> Dict[str, Any]:
    situaciones: List[Dict[str, Any]] = []
    situaciones.extend(datos.get("stock", []) or [])
    situaciones.extend(datos.get("produccion", []) or [])
    situaciones.extend(datos.get("eventos", []) or [])
    situaciones.extend(datos.get("compras", []) or [])
    situaciones.extend(datos.get("costes", []) or [])
    situaciones.extend(datos.get("alertas", []) or [])

    decisiones = generar_decisiones_operativas(situaciones)
    tareas = []
    compras = []
    produccion = []
    incidencias = []

    for d in decisiones["decisiones"]:
        accion = d["accion_recomendada"]
        if "compra" in accion or "stock" in accion:
            compras.append(d)
        elif "produccion" in accion or "evento" in accion:
            produccion.append(d)
        elif d["prioridad"] in {"critica", "alta"}:
            incidencias.append(d)
        tareas.append({"prioridad": d["prioridad"], "modulo": d["modulo"], "accion": accion, "descripcion": d["descripcion"]})

    return {
        "restaurante": datos.get("restaurante", "Restaurante"),
        "fecha": datos.get("fecha", "hoy"),
        "total_tareas": len(tareas),
        "tareas": tareas,
        "compras": compras,
        "produccion": produccion,
        "incidencias": incidencias,
        "decisiones": decisiones,
        "resumen_jefe_cocina": explicar_decisiones_como_jefe(decisiones["decisiones"], limite=5),
    }


def formatear_flujo_diario(flujo: Dict[str, Any]) -> str:
    lineas = [
        "=== FLUJO DIARIO HOST AI ===",
        f"Restaurante: {flujo.get('restaurante')}",
        f"Fecha: {flujo.get('fecha')}",
        f"Tareas detectadas: {flujo.get('total_tareas', 0)}",
        "",
        "Prioridades:",
    ]
    for tarea in flujo.get("tareas", [])[:8]:
        lineas.append(f"- [{tarea['prioridad']}] {tarea['modulo']}: {tarea['descripcion']} -> {tarea['accion']}")
    lineas.append("")
    lineas.append(flujo.get("resumen_jefe_cocina", ""))
    return "\n".join(lineas)
