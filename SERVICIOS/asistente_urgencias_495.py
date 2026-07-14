from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


PRIORIDAD_PESO = {"critica": 4, "alta": 3, "media": 2, "baja": 1}


def _normalizar_numero(valor: Any, defecto: float = 0.0) -> float:
    try:
        if valor is None or valor == "":
            return defecto
        return float(valor)
    except (TypeError, ValueError):
        return defecto


def _prioridad_por_puntos(puntos: int) -> str:
    if puntos >= 90:
        return "critica"
    if puntos >= 60:
        return "alta"
    if puntos >= 30:
        return "media"
    return "baja"


def detectar_urgencia(situacion: Dict[str, Any]) -> Dict[str, Any]:
    """Detecta una urgencia operativa sin ejecutar cambios reales.

    Está pensado como capa de seguridad para Host AI 4.9: analiza señales de
    stock, eventos, producción, proveedores y rentabilidad y devuelve una acción
    priorizada que el usuario puede confirmar después.
    """
    modulo = str(situacion.get("modulo", "general")).lower()
    nombre = situacion.get("nombre") or situacion.get("descripcion") or "Incidencia operativa"
    puntos = 0
    motivos: List[str] = []
    acciones: List[str] = []

    stock_actual = _normalizar_numero(situacion.get("stock_actual"), 999999)
    stock_minimo = _normalizar_numero(situacion.get("stock_minimo"), -1)
    stock_necesario = _normalizar_numero(situacion.get("stock_necesario"), 0)
    horas = int(_normalizar_numero(situacion.get("horas_hasta_servicio"), 999))

    if situacion.get("rotura_stock") or stock_actual <= stock_minimo or (stock_necesario and stock_actual < stock_necesario):
        puntos += 40
        motivos.append("riesgo de rotura de stock")
        acciones.append("confirmar stock real y preparar compra urgente")

    if situacion.get("evento_proximo") or horas <= 24:
        puntos += 25
        motivos.append("servicio o evento próximo")
        acciones.append("validar producción y compras del evento")

    if situacion.get("produccion_bloqueada") or situacion.get("conflicto_recurso"):
        puntos += 35
        motivos.append("producción bloqueada")
        acciones.append("replanificar producción y liberar recurso crítico")

    if situacion.get("proveedor_no_confirmado") or situacion.get("pedido_pendiente"):
        puntos += 20
        motivos.append("proveedor o pedido pendiente")
        acciones.append("contactar proveedor y confirmar entrega")

    if situacion.get("margen_bajo") or _normalizar_numero(situacion.get("margen"), 1) < 0.20:
        puntos += 15
        motivos.append("impacto económico")
        acciones.append("revisar precio, escandallo o alternativa de proveedor")

    if situacion.get("incidencia_cliente"):
        puntos += 30
        motivos.append("incidencia con cliente")
        acciones.append("avisar responsable y preparar solución antes del servicio")

    prioridad = _prioridad_por_puntos(puntos)
    if not acciones:
        acciones.append("mantener seguimiento")
    if not motivos:
        motivos.append("sin señales críticas")

    return {
        "nombre": nombre,
        "modulo": modulo,
        "puntuacion": puntos,
        "prioridad": prioridad,
        "motivos": motivos,
        "acciones_recomendadas": acciones,
        "accion_principal": acciones[0],
        "requiere_confirmacion": prioridad in {"critica", "alta"},
    }


def detectar_urgencias(situaciones: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    urgencias = [detectar_urgencia(s) for s in situaciones]
    urgencias.sort(key=lambda u: (PRIORIDAD_PESO.get(u["prioridad"], 0), u["puntuacion"]), reverse=True)
    return {
        "total_urgencias": len(urgencias),
        "criticas": [u for u in urgencias if u["prioridad"] == "critica"],
        "altas": [u for u in urgencias if u["prioridad"] == "alta"],
        "urgencias": urgencias,
        "primera_accion": urgencias[0] if urgencias else None,
    }


def generar_resumen_urgencias(resultado: Dict[str, Any], limite: int = 5) -> str:
    urgencias = resultado.get("urgencias", [])[:limite]
    if not urgencias:
        return "No hay urgencias operativas detectadas."

    lineas = ["=== ASISTENTE DE URGENCIAS HOST AI ==="]
    for urgencia in urgencias:
        motivos = ", ".join(urgencia.get("motivos", []))
        lineas.append(
            f"- [{urgencia['prioridad'].upper()}] {urgencia['nombre']} | "
            f"{motivos} -> {urgencia['accion_principal']}"
        )
    return "\n".join(lineas)
