from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional
import re


AREAS_CLAVE = {
    "eventos": ["evento", "boda", "banquete", "catering", "comunion", "comunión", "pax", "personas"],
    "produccion": ["produc", "elabor", "preparar", "planning", "planificar", "cocina", "servicio"],
    "stock": ["stock", "almacen", "almacén", "falt", "queda", "rotura", "mercancia", "mercancía"],
    "compras": ["compr", "pedido", "proveedor", "makro", "factura", "albaran", "albarán"],
    "rentabilidad": ["margen", "coste", "precio", "rentabilidad", "beneficio", "perder", "ganar"],
    "ia": ["recomienda", "decide", "prioridad", "urgente", "que hago", "qué hago", "ayuda"],
}

ORDEN_AREAS = ["ia", "eventos", "produccion", "stock", "compras", "rentabilidad"]


def _normalizar_texto(texto: str) -> str:
    return (texto or "").strip().lower()


def detectar_areas_solicitud(solicitud: str) -> List[str]:
    """Detecta áreas operativas mencionadas en una solicitud natural.

    Este núcleo no ejecuta cambios. Solo entiende qué partes de Host AI deberían
    intervenir en una conversación o flujo de trabajo.
    """
    texto = _normalizar_texto(solicitud)
    areas: List[str] = []
    for area in ORDEN_AREAS:
        claves = AREAS_CLAVE[area]
        if any(clave in texto for clave in claves):
            areas.append(area)

    # Si el usuario habla de un servicio/evento con personas, normalmente hay que
    # activar producción, stock, compras y rentabilidad aunque no las nombre.
    if "eventos" in areas:
        for area in ["produccion", "stock", "compras", "rentabilidad"]:
            if area not in areas:
                areas.append(area)

    if not areas:
        areas = ["ia"]
    return areas


def extraer_datos_basicos_solicitud(solicitud: str) -> Dict[str, Any]:
    texto = _normalizar_texto(solicitud)
    numeros = [int(n) for n in re.findall(r"\b\d+\b", texto)]
    personas: Optional[int] = None
    for n in numeros:
        if n >= 10:
            personas = n
            break
    urgencia = any(p in texto for p in ["hoy", "mañana", "urgente", "ya", "esta noche", "sábado", "domingo"])
    return {
        "personas_estimadas": personas,
        "urgente": urgencia,
        "texto_original": solicitud,
    }


def construir_contexto_operativo(solicitud: str, datos: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    datos = datos or {}
    areas = detectar_areas_solicitud(solicitud)
    basicos = extraer_datos_basicos_solicitud(solicitud)
    situaciones: List[Dict[str, Any]] = []

    for area in areas:
        if area == "ia":
            continue
        situaciones.append({
            "modulo": area,
            "descripcion": f"Solicitud relacionada con {area}: {solicitud}",
            "evento_proximo": area == "eventos" and basicos["urgente"],
            "produccion_bloqueada": False,
            "alerta": basicos["urgente"],
            "horas_hasta_servicio": 12 if basicos["urgente"] else 72,
        })

    contexto = {
        "restaurante": datos.get("restaurante", "Restaurante"),
        "solicitud": solicitud,
        "areas_detectadas": areas,
        "datos_extraidos": basicos,
        "situaciones": situaciones,
        "datos": datos,
    }
    return contexto


def generar_plan_nucleo(contexto: Dict[str, Any]) -> Dict[str, Any]:
    areas = contexto.get("areas_detectadas", [])
    pasos: List[Dict[str, Any]] = []

    mapa_pasos = {
        "eventos": "Crear o revisar el evento y sus datos básicos.",
        "produccion": "Calcular producción necesaria, tiempos y prioridades.",
        "stock": "Comprobar stock disponible y artículos críticos.",
        "compras": "Detectar faltantes y preparar pedidos sugeridos.",
        "rentabilidad": "Estimar coste, margen y viabilidad económica.",
        "ia": "Analizar la intención y decidir qué flujo operativo activar.",
    }

    for area in areas:
        pasos.append({
            "area": area,
            "accion": mapa_pasos.get(area, "Revisar información operativa."),
            "ejecutar_automaticamente": False,
            "requiere_confirmacion": True,
        })

    return {
        "total_pasos": len(pasos),
        "pasos": pasos,
        "modo": "propuesta_segura",
    }


def evaluar_con_motores_existentes(contexto: Dict[str, Any]) -> Dict[str, Any]:
    """Usa motores existentes si están disponibles, sin acoplar el núcleo a ellos.

    Si algún módulo no existe o falla, el núcleo continúa devolviendo una propuesta
    básica. Así el 5.1 queda estable y preparado para evolucionar.
    """
    resultado: Dict[str, Any] = {"decisiones": None, "recomendaciones": None, "panel": None}
    situaciones = contexto.get("situaciones", [])
    datos = contexto.get("datos", {}) or {}

    try:
        from SERVICIOS.motor_decisiones_operativas_491 import generar_decisiones_operativas
        resultado["decisiones"] = generar_decisiones_operativas(situaciones)
    except Exception as exc:  # pragma: no cover - robustez defensiva
        resultado["decisiones_error"] = str(exc)

    try:
        from SERVICIOS.recomendaciones_inteligentes_496 import analizar_recomendaciones
        resultado["recomendaciones"] = analizar_recomendaciones(datos)
    except Exception as exc:  # pragma: no cover
        resultado["recomendaciones_error"] = str(exc)

    try:
        from SERVICIOS.panel_ia_central_497 import generar_panel_ia_central
        panel_datos = dict(datos)
        for clave in ["stock", "produccion", "eventos", "compras", "rentabilidad"]:
            panel_datos.setdefault(clave, [])
        resultado["panel"] = generar_panel_ia_central(panel_datos)
    except Exception as exc:  # pragma: no cover
        resultado["panel_error"] = str(exc)

    return resultado


def procesar_solicitud_nucleo_ia(solicitud: str, datos: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    contexto = construir_contexto_operativo(solicitud, datos)
    plan = generar_plan_nucleo(contexto)
    motores = evaluar_con_motores_existentes(contexto)
    return {
        "version": "5.1",
        "tipo": "nucleo_ia_host_ai",
        "estado": "ok",
        "contexto": contexto,
        "plan": plan,
        "motores": motores,
        "respuesta": redactar_respuesta_nucleo(contexto, plan, motores),
    }


def redactar_respuesta_nucleo(contexto: Dict[str, Any], plan: Dict[str, Any], motores: Dict[str, Any]) -> str:
    areas = ", ".join(contexto.get("areas_detectadas", []))
    datos = contexto.get("datos_extraidos", {})
    personas = datos.get("personas_estimadas")

    lineas = [
        "=== HOST AI 5.1 - NUCLEO IA ===",
        f"Solicitud: {contexto.get('solicitud')}",
        f"Áreas detectadas: {areas}",
    ]
    if personas:
        lineas.append(f"Personas estimadas: {personas}")

    lineas.append("")
    lineas.append("Plan propuesto:")
    for paso in plan.get("pasos", []):
        lineas.append(f"- {paso['area']}: {paso['accion']}")

    decisiones = motores.get("decisiones") or {}
    siguiente = decisiones.get("siguiente_accion") if isinstance(decisiones, dict) else None
    if siguiente:
        lineas.append("")
        lineas.append("Primera prioridad detectada:")
        lineas.append(f"- [{siguiente.get('prioridad')}] {siguiente.get('descripcion')} -> {siguiente.get('accion_recomendada')}")

    lineas.append("")
    lineas.append("Modo seguro: no se ejecuta ninguna acción sin confirmación.")
    return "\n".join(lineas)
