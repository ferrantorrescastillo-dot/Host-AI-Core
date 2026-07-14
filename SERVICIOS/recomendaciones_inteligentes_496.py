from __future__ import annotations

from typing import Any, Dict, Iterable, List


def _numero(valor: Any, defecto: float = 0.0) -> float:
    try:
        if valor is None or valor == "":
            return defecto
        return float(valor)
    except (TypeError, ValueError):
        return defecto


def generar_recomendacion(area: str, descripcion: str, impacto: str, accion: str, prioridad: str = "media") -> Dict[str, Any]:
    return {
        "area": area,
        "descripcion": descripcion,
        "impacto": impacto,
        "accion_recomendada": accion,
        "prioridad": prioridad,
    }


def analizar_recomendaciones(datos: Dict[str, Any]) -> Dict[str, Any]:
    """Genera recomendaciones de mejora con datos de compras, producción y rentabilidad."""
    recomendaciones: List[Dict[str, Any]] = []

    for item in datos.get("stock", []) or []:
        nombre = item.get("nombre") or item.get("descripcion") or "Artículo"
        stock_actual = _numero(item.get("stock_actual"), 0)
        stock_minimo = _numero(item.get("stock_minimo"), 0)
        rotacion = _numero(item.get("rotacion"), 0)
        if stock_minimo and stock_actual < stock_minimo:
            recomendaciones.append(generar_recomendacion(
                "stock",
                f"{nombre} está por debajo del mínimo.",
                "riesgo de rotura en servicio",
                "generar pedido sugerido y validar proveedor",
                "alta",
            ))
        if stock_actual > stock_minimo * 4 and rotacion < 1 and stock_minimo:
            recomendaciones.append(generar_recomendacion(
                "stock",
                f"{nombre} parece sobrecomprado para su rotación.",
                "dinero inmovilizado en almacén",
                "reducir próxima compra o buscar salida en menú",
                "media",
            ))

    for compra in datos.get("compras", []) or []:
        nombre = compra.get("nombre") or compra.get("articulo") or "Artículo"
        variacion = _numero(compra.get("variacion_precio"), 0)
        if variacion >= 0.10:
            recomendaciones.append(generar_recomendacion(
                "compras",
                f"{nombre} ha subido un {variacion:.0%}.",
                "bajada directa de margen",
                "comparar proveedores o renegociar precio",
                "alta" if variacion >= 0.20 else "media",
            ))

    for produccion in datos.get("produccion", []) or []:
        nombre = produccion.get("nombre") or produccion.get("elaboracion") or "Elaboración"
        retraso = _numero(produccion.get("retraso_minutos"), 0)
        merma = _numero(produccion.get("merma"), 0)
        if retraso > 30:
            recomendaciones.append(generar_recomendacion(
                "produccion",
                f"{nombre} acumula {int(retraso)} minutos de retraso.",
                "riesgo de llegar tarde al servicio",
                "replanificar tareas y asignar refuerzo",
                "alta",
            ))
        if merma > 0.08:
            recomendaciones.append(generar_recomendacion(
                "produccion",
                f"{nombre} tiene una merma elevada ({merma:.0%}).",
                "pérdida económica y posible fallo de proceso",
                "revisar receta, porcionado y conservación",
                "media",
            ))

    for plato in datos.get("rentabilidad", []) or []:
        nombre = plato.get("nombre") or plato.get("plato") or "Plato"
        margen = _numero(plato.get("margen"), 1)
        ventas = _numero(plato.get("ventas"), 0)
        if margen < 0.25 and ventas > 0:
            recomendaciones.append(generar_recomendacion(
                "rentabilidad",
                f"{nombre} vende pero deja poco margen ({margen:.0%}).",
                "muchas ventas con poca ganancia",
                "subir precio, ajustar ración o cambiar proveedor",
                "alta",
            ))
        elif margen > 0.60 and ventas < 5:
            recomendaciones.append(generar_recomendacion(
                "carta",
                f"{nombre} tiene buen margen pero pocas ventas.",
                "oportunidad comercial desaprovechada",
                "mejorar venta sugerida o posición en carta",
                "media",
            ))

    recomendaciones.sort(key=lambda r: {"alta": 3, "media": 2, "baja": 1}.get(r["prioridad"], 0), reverse=True)
    return {
        "total_recomendaciones": len(recomendaciones),
        "recomendaciones": recomendaciones,
        "prioritarias": [r for r in recomendaciones if r["prioridad"] == "alta"],
    }


def formatear_recomendaciones(resultado: Dict[str, Any], limite: int = 8) -> str:
    recomendaciones = resultado.get("recomendaciones", [])[:limite]
    if not recomendaciones:
        return "No hay recomendaciones inteligentes pendientes."
    lineas = ["=== RECOMENDACIONES INTELIGENTES HOST AI ==="]
    for r in recomendaciones:
        lineas.append(
            f"- [{r['prioridad'].upper()}] {r['area']}: {r['descripcion']} "
            f"Impacto: {r['impacto']}. Acción: {r['accion_recomendada']}."
        )
    return "\n".join(lineas)
