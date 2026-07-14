from __future__ import annotations

from typing import Dict, Any, Iterable, List


def evaluar_alerta_rentabilidad(item: Dict[str, Any], margen_minimo: float = 0.60) -> Dict[str, Any]:
    nombre = item.get("nombre") or item.get("plato") or "sin nombre"
    precio = float(item.get("precio_venta", 0))
    coste = float(item.get("coste", 0))
    margen = 0.0 if precio <= 0 else round((precio - coste) / precio, 4)
    estado = "ok"
    severidad = "baja"
    mensaje = f"{nombre}: margen correcto ({margen:.1%})."
    if precio <= 0:
        estado, severidad, mensaje = "alerta", "alta", f"{nombre}: precio de venta no válido."
    elif margen < margen_minimo:
        estado = "alerta"
        severidad = "alta" if margen < margen_minimo - 0.15 else "media"
        mensaje = f"{nombre}: margen {margen:.1%} por debajo del mínimo {margen_minimo:.1%}."
    return {"nombre": nombre, "precio_venta": precio, "coste": coste, "margen": margen, "estado": estado, "severidad": severidad, "mensaje": mensaje}


def generar_alertas_rentabilidad(items: Iterable[Dict[str, Any]], margen_minimo: float = 0.60) -> Dict[str, Any]:
    evaluaciones = [evaluar_alerta_rentabilidad(i, margen_minimo) for i in items]
    alertas = [e for e in evaluaciones if e["estado"] == "alerta"]
    return {"total_items": len(evaluaciones), "total_alertas": len(alertas), "alertas": alertas, "evaluaciones": evaluaciones}


def resumen_alertas(alertas: Dict[str, Any]) -> str:
    total = int(alertas.get("total_alertas", 0))
    if total == 0:
        return "No hay alertas de rentabilidad."
    primeras = alertas.get("alertas", [])[:3]
    detalle = " | ".join(a["mensaje"] for a in primeras)
    return f"Hay {total} alertas de rentabilidad. {detalle}"
