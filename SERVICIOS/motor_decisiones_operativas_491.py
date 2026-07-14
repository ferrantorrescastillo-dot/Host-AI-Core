from __future__ import annotations

from typing import Dict, Any, Iterable, List


def _nivel_prioridad(puntos: int) -> str:
    if puntos >= 80:
        return "critica"
    if puntos >= 55:
        return "alta"
    if puntos >= 30:
        return "media"
    return "baja"


def evaluar_decision_operativa(situacion: Dict[str, Any]) -> Dict[str, Any]:
    """Evalúa una situación operativa y devuelve una decisión priorizada.

    La función no ejecuta cambios. Solo decide qué conviene hacer primero usando
    señales de stock, producción, eventos, compras, costes y alertas.
    """
    modulo = str(situacion.get("modulo", "general")).lower()
    descripcion = situacion.get("descripcion") or situacion.get("nombre") or "situación operativa"
    puntos = 0
    motivos: List[str] = []

    if situacion.get("rotura_stock") or float(situacion.get("stock_actual", 999999)) <= float(situacion.get("stock_minimo", -1)):
        puntos += 35
        motivos.append("riesgo de rotura de stock")
    if situacion.get("evento_proximo") or int(situacion.get("horas_hasta_servicio", 999)) <= 24:
        puntos += 25
        motivos.append("servicio o evento próximo")
    if situacion.get("produccion_bloqueada") or situacion.get("conflicto_recurso"):
        puntos += 35
        motivos.append("producción bloqueada o recurso en conflicto")
    if situacion.get("margen_bajo") or float(situacion.get("margen", 1)) < 0.20:
        puntos += 15
        motivos.append("impacto económico")
    if situacion.get("alerta"):
        puntos += 10
        motivos.append("alerta activa")

    accion = "revisar"
    if modulo in {"stock", "compras"} and puntos >= 30:
        accion = "proponer_compra_o_entrada_stock"
    elif modulo == "produccion" and puntos >= 30:
        accion = "replanificar_produccion"
    elif modulo == "eventos" and puntos >= 30:
        accion = "preparar_plan_evento"
    elif modulo in {"costes", "rentabilidad"} and puntos >= 30:
        accion = "revisar_precio_o_escandallo"

    return {
        "descripcion": descripcion,
        "modulo": modulo,
        "puntuacion": puntos,
        "prioridad": _nivel_prioridad(puntos),
        "accion_recomendada": accion,
        "motivos": motivos or ["sin señales críticas"],
    }


def generar_decisiones_operativas(situaciones: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    decisiones = [evaluar_decision_operativa(s) for s in situaciones]
    decisiones.sort(key=lambda d: d["puntuacion"], reverse=True)
    return {
        "total_decisiones": len(decisiones),
        "criticas": [d for d in decisiones if d["prioridad"] == "critica"],
        "decisiones": decisiones,
        "siguiente_accion": decisiones[0] if decisiones else None,
    }


def resumen_decisiones_operativas(resultado: Dict[str, Any]) -> str:
    siguiente = resultado.get("siguiente_accion")
    if not siguiente:
        return "No hay decisiones operativas pendientes."
    return (
        f"Prioridad {siguiente['prioridad']}: {siguiente['descripcion']} -> "
        f"{siguiente['accion_recomendada']} ({', '.join(siguiente['motivos'])})."
    )
