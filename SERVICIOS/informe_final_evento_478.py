# Host AI 4.7.8 - Informe final inteligente de evento


def calcular_resultado_evento(evento, costes=None, ingresos=None, incidencias=None):
    personas = int(evento.get("personas") or 0)
    costes = costes or {}
    incidencias = incidencias or []
    ingreso_total = float(ingresos if ingresos is not None else evento.get("presupuesto") or 0)
    coste_total = sum(float(v or 0) for v in costes.values())
    beneficio = ingreso_total - coste_total
    margen = (beneficio / ingreso_total * 100) if ingreso_total else 0
    coste_persona = (coste_total / personas) if personas else 0
    ingreso_persona = (ingreso_total / personas) if personas else 0
    return {
        "ok": True,
        "id_evento": evento.get("id_evento"),
        "nombre": evento.get("nombre"),
        "personas": personas,
        "ingreso_total": round(ingreso_total, 2),
        "coste_total": round(coste_total, 2),
        "beneficio": round(beneficio, 2),
        "margen_porcentaje": round(margen, 2),
        "coste_por_persona": round(coste_persona, 2),
        "ingreso_por_persona": round(ingreso_persona, 2),
        "costes": costes,
        "incidencias": incidencias,
        "estado_economico": clasificar_resultado(margen),
    }


def clasificar_resultado(margen):
    margen = float(margen or 0)
    if margen >= 35:
        return "muy_rentable"
    if margen >= 22:
        return "rentable"
    if margen >= 10:
        return "ajustado"
    return "revisar"


def generar_recomendaciones_evento(informe):
    recomendaciones = []
    if informe.get("margen_porcentaje", 0) < 22:
        recomendaciones.append("Revisar precio de venta o coste de menu para proximos eventos similares.")
    if informe.get("costes", {}).get("personal", 0) > informe.get("coste_total", 1) * 0.35:
        recomendaciones.append("El coste de personal pesa mucho; revisar horas y dimensionamiento del equipo.")
    if informe.get("incidencias"):
        recomendaciones.append("Revisar incidencias antes de repetir este formato de evento.")
    if not recomendaciones:
        recomendaciones.append("Evento correcto. Usar como referencia para presupuestos similares.")
    return recomendaciones


def formatear_informe_final_evento(informe):
    lineas = [
        "INFORME FINAL EVENTO",
        f"Evento: {informe.get('nombre')}",
        f"Personas: {informe.get('personas')}",
        f"Ingresos: {informe.get('ingreso_total')} €",
        f"Costes: {informe.get('coste_total')} €",
        f"Beneficio: {informe.get('beneficio')} €",
        f"Margen: {informe.get('margen_porcentaje')} %",
        f"Estado: {informe.get('estado_economico')}",
        "Recomendaciones:",
    ]
    for rec in generar_recomendaciones_evento(informe):
        lineas.append(f"- {rec}")
    return "\n".join(lineas)
