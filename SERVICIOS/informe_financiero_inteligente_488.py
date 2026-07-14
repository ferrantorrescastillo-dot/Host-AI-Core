from __future__ import annotations

from typing import Dict, Any, Iterable, List


def generar_informe_financiero(datos: Dict[str, Any]) -> Dict[str, Any]:
    ventas = float(datos.get("ventas", 0))
    coste_materia = float(datos.get("coste_materia", 0))
    coste_personal = float(datos.get("coste_personal", 0))
    mermas = float(datos.get("mermas", 0))
    otros_costes = float(datos.get("otros_costes", 0))
    coste_total = round(coste_materia + coste_personal + mermas + otros_costes, 4)
    beneficio = round(ventas - coste_total, 4)
    margen = 0.0 if ventas <= 0 else round(beneficio / ventas, 4)
    return {
        "ventas": ventas,
        "coste_total": coste_total,
        "coste_materia": coste_materia,
        "coste_personal": coste_personal,
        "mermas": mermas,
        "otros_costes": otros_costes,
        "beneficio": beneficio,
        "margen": margen,
        "recomendaciones": generar_recomendaciones_financieras(ventas, coste_materia, coste_personal, mermas, beneficio, margen),
    }


def generar_recomendaciones_financieras(ventas: float, coste_materia: float, coste_personal: float, mermas: float, beneficio: float, margen: float) -> List[str]:
    recs: List[str] = []
    if margen < 0.15:
        recs.append("Margen bajo: revisar precios de venta, compras y productividad.")
    if ventas > 0 and coste_materia / ventas > 0.35:
        recs.append("Coste de materia prima alto: revisar escandallos y proveedores.")
    if ventas > 0 and coste_personal / ventas > 0.30:
        recs.append("Coste de personal alto: revisar planificación y horas improductivas.")
    if mermas > 0:
        recs.append("Hay coste por mermas: revisar sobreproducción, caducidades y porcionado.")
    if beneficio > 0 and not recs:
        recs.append("Rentabilidad correcta. Mantener seguimiento semanal.")
    if beneficio <= 0:
        recs.append("Resultado negativo: activar revisión urgente de costes y precios.")
    return recs


def formatear_informe_financiero(informe: Dict[str, Any]) -> str:
    lineas = [
        "=== INFORME FINANCIERO HOST AI ===",
        f"Ventas: {informe.get('ventas', 0):.2f} €",
        f"Coste total: {informe.get('coste_total', 0):.2f} €",
        f"Beneficio: {informe.get('beneficio', 0):.2f} €",
        f"Margen: {informe.get('margen', 0):.1%}",
        "Recomendaciones:",
    ]
    lineas.extend(f"- {r}" for r in informe.get("recomendaciones", []))
    return "\n".join(lineas)
