"""Host AI 5.3.2 - Ejecutor inteligente del flujo operativo.

Ejecuta de forma segura un flujo generado por 5.3.1. En esta primera versión,
las acciones críticas quedan simuladas/pendientes para evitar modificar datos sin
confirmaciones específicas de cada motor.
"""
from __future__ import annotations

from typing import Any, Dict, List


def _ejecutar_paso_simulado(paso: Dict[str, Any], datos: Dict[str, Any]) -> Dict[str, Any]:
    codigo = paso.get("codigo")
    nombre = paso.get("nombre")
    requiere_confirmacion = bool(paso.get("requiere_confirmacion"))
    modifica_datos = bool(paso.get("modifica_datos"))

    if requiere_confirmacion and modifica_datos:
        estado = "pendiente_confirmacion_especifica"
        detalle = f"{nombre}: requiere confirmación antes de modificar datos reales."
    else:
        estado = "ok_simulado"
        detalle = f"{nombre}: validado en modo seguro."

    # Salidas operativas orientativas, no inventa datos de stock/precio reales.
    if codigo == "STOCK_REVISAR":
        detalle = "Stock: revisión preparada. Para datos reales se debe conectar al inventario activo."
    elif codigo == "COMPRAS_PREPARAR":
        detalle = "Compras: pedido preliminar preparado pendiente de stock real y confirmación."
    elif codigo == "COSTES_CALCULAR":
        detalle = "Rentabilidad: cálculo preparado pendiente de escandallos/precios reales."
    elif codigo == "PRODUCCION_PLAN":
        detalle = "Producción: planning preliminar preparado con los datos mínimos del evento."

    return {
        "codigo": codigo,
        "nombre": nombre,
        "estado": estado,
        "detalle": detalle,
        "modifico_datos": False,
    }


def ejecutar_flujo_operativo(flujo: Dict[str, Any], confirmar: bool = False) -> Dict[str, Any]:
    """Ejecuta el flujo en modo seguro.

    confirmar=True permite avanzar sobre pasos no destructivos, pero los pasos que
    modifican datos reales siguen quedando marcados para confirmación específica.
    """
    if not flujo.get("ok"):
        return {
            "ok": False,
            "estado": "no_ejecutado",
            "mensaje": "No se puede ejecutar el flujo porque faltan datos mínimos.",
            "resultados": [],
        }

    resultados: List[Dict[str, Any]] = []
    for paso in flujo.get("pasos", []):
        resultados.append(_ejecutar_paso_simulado(paso, flujo.get("datos", {})))

    pendientes = [r for r in resultados if r["estado"] == "pendiente_confirmacion_especifica"]
    return {
        "ok": True,
        "estado": "ejecutado_modo_seguro",
        "confirmado": confirmar,
        "resultados": resultados,
        "pendientes_confirmacion": pendientes,
        "modifico_datos_reales": False,
        "mensaje": "Flujo ejecutado en modo seguro. No se han modificado datos reales.",
    }


def formatear_ejecucion_flujo(resultado: Dict[str, Any]) -> str:
    lineas: List[str] = []
    lineas.append("HOST AI 5.3.2 - EJECUCIÓN DEL FLUJO")
    lineas.append("-" * 60)
    lineas.append(resultado.get("mensaje", ""))
    lineas.append("")

    for item in resultado.get("resultados", []):
        if item.get("estado") == "pendiente_confirmacion_especifica":
            icono = "!"
        else:
            icono = "OK"
        lineas.append(f"[{icono}] {item.get('detalle')}")

    pendientes = resultado.get("pendientes_confirmacion", [])
    if pendientes:
        lineas.append("")
        lineas.append("Pendiente de confirmación antes de modificar datos reales:")
        for item in pendientes:
            lineas.append(f"- {item.get('nombre')}")

    return "\n".join(lineas)
