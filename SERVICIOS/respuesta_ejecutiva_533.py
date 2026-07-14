"""Host AI 5.3.3 - Respuesta ejecutiva inteligente.

Convierte un flujo operativo y su ejecución segura en una respuesta de jefe de
cocina: clara, accionable y sin inventar datos que no hayan sido devueltos por
los motores existentes.
"""
from __future__ import annotations

from typing import Any, Dict, List


def _datos_evento(flujo: Dict[str, Any]) -> Dict[str, Any]:
    return dict(flujo.get("datos") or {})


def _resultados(ejecucion: Dict[str, Any]) -> List[Dict[str, Any]]:
    return list(ejecucion.get("resultados") or [])


def _contar(resultados: List[Dict[str, Any]], texto: str) -> int:
    t = texto.lower()
    return sum(1 for r in resultados if t in str(r.get("codigo", "")).lower() or t in str(r.get("detalle", "")).lower())


def generar_respuesta_ejecutiva_evento(flujo: Dict[str, Any], ejecucion: Dict[str, Any]) -> Dict[str, Any]:
    """Genera un resumen ejecutivo seguro para eventos.

    No calcula compras, stock ni costes reales si el flujo todavía trabaja en
    modo simulado. En ese caso lo deja explícitamente indicado.
    """
    if not flujo.get("ok"):
        return {
            "ok": False,
            "estado": "sin_flujo",
            "mensaje": "No puedo generar una respuesta ejecutiva porque todavía faltan datos mínimos.",
            "lineas": [],
        }

    datos = _datos_evento(flujo)
    resultados = _resultados(ejecucion)
    pendientes = list(ejecucion.get("pendientes_confirmacion") or [])
    pasos = list(flujo.get("pasos") or [])

    lineas: List[str] = []
    lineas.append("Perfecto. Ya tengo el evento suficientemente definido para trabajar sin inventar datos.")
    lineas.append("")
    lineas.append("RESUMEN DEL EVENTO")
    lineas.append(f"- Tipo: {datos.get('tipo', 'evento')}")
    lineas.append(f"- Personas: {datos.get('personas', 'pendiente')}")
    lineas.append(f"- Fecha: {datos.get('fecha', 'pendiente')}")
    lineas.append(f"- Hora servicio: {datos.get('hora_servicio', 'pendiente')}")
    lineas.append(f"- Menú: {datos.get('menu', 'pendiente')}")
    lineas.append(f"- Lugar: {datos.get('lugar', 'pendiente')}")
    lineas.append(f"- Restricciones: {datos.get('restricciones', 'pendiente')}")
    lineas.append("")

    lineas.append("FLUJO PREPARADO")
    lineas.append(f"- Pasos generados: {len(pasos)}")
    lineas.append(f"- Pasos revisados en modo seguro: {len(resultados)}")
    lineas.append(f"- Acciones pendientes de confirmación: {len(pendientes)}")
    lineas.append("")

    lineas.append("LECTURA OPERATIVA")
    if _contar(resultados, "produccion") or _contar(resultados, "producción"):
        lineas.append("- Producción: planning preliminar preparado con los datos mínimos del evento.")
    if _contar(resultados, "stock"):
        lineas.append("- Stock: revisión preparada. Para cantidades reales necesito consultar el inventario activo.")
    if _contar(resultados, "compra"):
        lineas.append("- Compras: pedido preliminar preparado, pendiente de stock real y confirmación.")
    if _contar(resultados, "rentabilidad") or _contar(resultados, "coste"):
        lineas.append("- Coste/rentabilidad: cálculo preparado, pendiente de escandallos y precios reales.")
    if not resultados:
        lineas.append("- Todavía no hay resultados de ejecución del flujo.")
    lineas.append("")

    riesgos = []
    if ejecucion.get("modifico_datos_reales") is False:
        riesgos.append("No se han modificado datos reales todavía.")
    if pendientes:
        riesgos.append("Hay acciones que requieren confirmación específica antes de escribir en el sistema.")
    if riesgos:
        lineas.append("CONTROL DE RIESGO")
        for riesgo in riesgos:
            lineas.append(f"- {riesgo}")
        lineas.append("")

    lineas.append("RECOMENDACIÓN")
    lineas.append("- Primero confirmaría las acciones críticas: crear evento, asociar menú y preparar compras.")
    lineas.append("- Después ejecutaría producción, stock, compras y rentabilidad en ese orden.")
    lineas.append("- No generaría pedidos ni cambios reales sin confirmación explícita.")

    return {
        "ok": True,
        "estado": "respuesta_ejecutiva_generada",
        "datos": datos,
        "pasos": len(pasos),
        "pendientes_confirmacion": pendientes,
        "lineas": lineas,
        "mensaje": "\n".join(lineas),
    }


def formatear_respuesta_ejecutiva(respuesta: Dict[str, Any]) -> str:
    return str(respuesta.get("mensaje") or "")


__all__ = ["generar_respuesta_ejecutiva_evento", "formatear_respuesta_ejecutiva"]
