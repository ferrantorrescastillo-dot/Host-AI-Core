"""Host AI 5.3.1 - Generador automático del flujo operativo.

Este servicio NO modifica datos reales. Su función es construir un flujo de trabajo
seguro a partir de datos mínimos ya recogidos por Host AI 5.2.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List


@dataclass
class PasoFlujo:
    orden: int
    codigo: str
    nombre: str
    modulo: str
    accion: str
    requiere_confirmacion: bool = False
    modifica_datos: bool = False


PASOS_FLUJO_COMPLETO = [
    PasoFlujo(1, "EVENTO_CREAR", "Crear o localizar evento", "4.7.1", "crear_evento", True, True),
    PasoFlujo(2, "MENU_ASOCIAR", "Asociar menú del evento", "4.7.2", "asociar_menu", True, True),
    PasoFlujo(3, "PRODUCCION_PLAN", "Generar producción del evento", "4.7.3 / 4.6", "planificar_produccion", False, False),
    PasoFlujo(4, "RECURSOS_REVISAR", "Revisar recursos y personal", "4.6.5 / 4.7.5", "revisar_recursos", False, False),
    PasoFlujo(5, "STOCK_REVISAR", "Consultar stock disponible", "4.3", "consultar_stock", False, False),
    PasoFlujo(6, "COMPRAS_PREPARAR", "Preparar compras necesarias", "4.7.4", "preparar_compras", True, False),
    PasoFlujo(7, "COSTES_CALCULAR", "Calcular coste y rentabilidad", "4.8", "calcular_rentabilidad", False, False),
    PasoFlujo(8, "PLANNING_GENERAR", "Generar planning operativo", "4.6.8 / 4.7.7", "generar_planning", False, False),
]


def _valor(datos: Dict[str, Any], *claves: str, defecto: str = "pendiente") -> Any:
    for clave in claves:
        valor = datos.get(clave)
        if valor not in (None, "", "pendiente"):
            return valor
    return defecto


def validar_datos_minimos_evento(datos_evento: Dict[str, Any]) -> Dict[str, Any]:
    """Comprueba si hay datos mínimos antes de generar un flujo completo."""
    requeridos = {
        "tipo": _valor(datos_evento, "tipo", "tipo_evento"),
        "personas": _valor(datos_evento, "personas", "pax"),
        "fecha": _valor(datos_evento, "fecha"),
        "hora_servicio": _valor(datos_evento, "hora_servicio", "hora"),
        "menu": _valor(datos_evento, "menu", "menú"),
        "lugar": _valor(datos_evento, "lugar", "ubicacion", "ubicación"),
        "restricciones": _valor(datos_evento, "restricciones", "alergias"),
        "objetivo": _valor(datos_evento, "objetivo"),
    }
    faltan = [k for k, v in requeridos.items() if v in (None, "", "pendiente")]
    return {"ok": not faltan, "datos": requeridos, "faltan": faltan}


def generar_flujo_operativo_evento(datos_evento: Dict[str, Any]) -> Dict[str, Any]:
    """Genera el flujo operativo completo sin ejecutar acciones reales."""
    validacion = validar_datos_minimos_evento(datos_evento)
    if not validacion["ok"]:
        return {
            "ok": False,
            "estado": "faltan_datos",
            "datos": validacion["datos"],
            "faltan": validacion["faltan"],
            "mensaje": "Faltan datos mínimos para generar el flujo operativo sin inventar información.",
            "pasos": [],
        }

    objetivo = str(validacion["datos"].get("objetivo", "")).lower()
    if "compra" in objetivo and "flujo" not in objetivo and "todo" not in objetivo:
        pasos = [p for p in PASOS_FLUJO_COMPLETO if p.codigo in {"STOCK_REVISAR", "COMPRAS_PREPARAR"}]
    elif "produccion" in objetivo or "producción" in objetivo:
        pasos = [p for p in PASOS_FLUJO_COMPLETO if p.codigo in {"EVENTO_CREAR", "MENU_ASOCIAR", "PRODUCCION_PLAN", "RECURSOS_REVISAR", "PLANNING_GENERAR"}]
    elif "coste" in objetivo or "rentabilidad" in objetivo:
        pasos = [p for p in PASOS_FLUJO_COMPLETO if p.codigo in {"EVENTO_CREAR", "MENU_ASOCIAR", "COSTES_CALCULAR"}]
    else:
        pasos = PASOS_FLUJO_COMPLETO

    return {
        "ok": True,
        "estado": "flujo_generado",
        "datos": validacion["datos"],
        "pasos": [asdict(p) for p in pasos],
        "modifica_datos_directamente": False,
        "requiere_confirmacion": any(p.requiere_confirmacion for p in pasos),
        "mensaje": "Flujo operativo generado. No se han modificado datos reales.",
    }


def formatear_flujo_operativo(flujo: Dict[str, Any]) -> str:
    datos = flujo.get("datos", {})
    lineas: List[str] = []
    lineas.append("HOST AI 5.3.1 - FLUJO OPERATIVO")
    lineas.append("-" * 60)
    lineas.append(f"Evento: {datos.get('tipo', 'pendiente')} | Pax: {datos.get('personas', 'pendiente')} | Fecha: {datos.get('fecha', 'pendiente')} | Hora: {datos.get('hora_servicio', 'pendiente')}")
    lineas.append(f"Lugar: {datos.get('lugar', 'pendiente')} | Menú: {datos.get('menu', 'pendiente')}")
    lineas.append("")
    if not flujo.get("ok"):
        lineas.append("Faltan datos mínimos:")
        for falta in flujo.get("faltan", []):
            lineas.append(f"- {falta}")
        return "\n".join(lineas)

    lineas.append("Plan generado:")
    for paso in flujo.get("pasos", []):
        marca = "[confirmar]" if paso.get("requiere_confirmacion") else "[seguro]"
        lineas.append(f"{paso['orden']}. {paso['nombre']} ({paso['modulo']}) {marca}")
    lineas.append("")
    lineas.append("No he modificado datos. El siguiente paso es confirmar la ejecución del flujo.")
    return "\n".join(lineas)
