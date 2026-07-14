from __future__ import annotations

from typing import Any, Dict, Iterable, List

from SERVICIOS.motor_decisiones_operativas_491 import generar_decisiones_operativas
from SERVICIOS.flujo_diario_automatico_494 import generar_flujo_diario


def _lista(datos: Dict[str, Any], clave: str) -> List[Dict[str, Any]]:
    valor = datos.get(clave, []) or []
    return list(valor) if isinstance(valor, Iterable) and not isinstance(valor, (str, bytes, dict)) else []


def generar_panel_ia_central(datos: Dict[str, Any]) -> Dict[str, Any]:
    """Construye una vista única de IA operativa para dirección de cocina.

    El panel no modifica datos: consolida alertas, stock, producción, eventos,
    rentabilidad y recomendaciones para que el usuario vea qué requiere atención.
    """
    flujo = generar_flujo_diario(datos)
    situaciones: List[Dict[str, Any]] = []
    for clave in ("stock", "produccion", "eventos", "compras", "costes", "rentabilidad", "alertas"):
        situaciones.extend(_lista(datos, clave))

    decisiones = generar_decisiones_operativas(situaciones)
    alertas = [d for d in decisiones.get("decisiones", []) if d.get("prioridad") in {"critica", "alta"}]

    recomendaciones = []
    try:
        from SERVICIOS.recomendaciones_inteligentes_496 import analizar_recomendaciones
        recomendaciones = analizar_recomendaciones(datos).get("recomendaciones", [])
    except Exception:
        recomendaciones = []

    urgencias = []
    try:
        from SERVICIOS.asistente_urgencias_495 import detectar_urgencias
        urgencias = detectar_urgencias(situaciones).get("urgencias", [])
    except Exception:
        urgencias = alertas

    estado = "estable"
    if any(u.get("prioridad") == "critica" for u in urgencias):
        estado = "critico"
    elif alertas or urgencias:
        estado = "atencion"

    return {
        "restaurante": datos.get("restaurante", "Restaurante"),
        "fecha": datos.get("fecha", "hoy"),
        "estado_general": estado,
        "total_alertas": len(alertas),
        "total_urgencias": len(urgencias),
        "total_recomendaciones": len(recomendaciones),
        "flujo_diario": flujo,
        "alertas_prioritarias": alertas[:8],
        "urgencias": urgencias[:8],
        "recomendaciones": recomendaciones[:8],
        "siguiente_accion": decisiones.get("siguiente_accion"),
    }


def formatear_panel_ia_central(panel: Dict[str, Any]) -> str:
    lineas = [
        "=== PANEL IA CENTRAL HOST AI ===",
        f"Restaurante: {panel.get('restaurante')}",
        f"Fecha: {panel.get('fecha')}",
        f"Estado general: {panel.get('estado_general')}",
        f"Alertas: {panel.get('total_alertas', 0)} | Urgencias: {panel.get('total_urgencias', 0)} | Recomendaciones: {panel.get('total_recomendaciones', 0)}",
        "",
        "Siguiente acción:",
    ]
    accion = panel.get("siguiente_accion")
    if accion:
        lineas.append(f"- [{accion.get('prioridad')}] {accion.get('descripcion')} -> {accion.get('accion_recomendada')}")
    else:
        lineas.append("- Sin acciones críticas pendientes.")

    if panel.get("alertas_prioritarias"):
        lineas.append("")
        lineas.append("Alertas prioritarias:")
        for alerta in panel["alertas_prioritarias"][:5]:
            lineas.append(f"- [{alerta.get('prioridad')}] {alerta.get('modulo')}: {alerta.get('descripcion')}")

    if panel.get("recomendaciones"):
        lineas.append("")
        lineas.append("Recomendaciones:")
        for rec in panel["recomendaciones"][:5]:
            lineas.append(f"- [{rec.get('prioridad')}] {rec.get('area')}: {rec.get('descripcion')}")

    return "\n".join(lineas)
