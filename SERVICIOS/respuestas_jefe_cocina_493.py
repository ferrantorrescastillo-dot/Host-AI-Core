from __future__ import annotations

from typing import Dict, Any, Iterable, List


def generar_respuesta_jefe_cocina(contexto: Dict[str, Any]) -> str:
    prioridad = contexto.get("prioridad", "media")
    problema = contexto.get("problema") or contexto.get("descripcion") or "situación pendiente"
    accion = contexto.get("accion") or contexto.get("accion_recomendada") or "revisar la operativa"
    motivos = contexto.get("motivos", []) or []
    modulo = contexto.get("modulo", "cocina")

    inicio = {
        "critica": "Esto hay que resolverlo ya.",
        "alta": "Esto debe ir entre las primeras prioridades.",
        "media": "Esto conviene dejarlo controlado durante el turno.",
        "baja": "Esto no bloquea el servicio, pero hay que tenerlo registrado.",
    }.get(str(prioridad).lower(), "Hay que revisarlo con criterio operativo.")

    razon = ""
    if motivos:
        razon = " Motivo: " + "; ".join(str(m) for m in motivos) + "."

    return f"{inicio} En {modulo}: {problema}. Acción recomendada: {accion}.{razon}"


def explicar_decisiones_como_jefe(decisiones: Iterable[Dict[str, Any]], limite: int = 5) -> str:
    lineas: List[str] = ["=== CRITERIO OPERATIVO HOST AI ==="]
    for decision in list(decisiones)[:limite]:
        lineas.append("- " + generar_respuesta_jefe_cocina(decision))
    if len(lineas) == 1:
        lineas.append("No hay decisiones relevantes que explicar.")
    return "\n".join(lineas)


def respuesta_urgente(problema: str, accion_inmediata: str, riesgo: str = "servicio") -> str:
    return (
        f"Prioridad máxima: {problema}. Primero asegura {riesgo}. "
        f"Después ejecuta: {accion_inmediata}. No esperes al cierre del turno para revisarlo."
    )
