# Host AI 4.7.5 - Organizacion inteligente de personal para eventos

from math import ceil


RATIOS_BASE = {
    "cocinero": 45,
    "ayudante_cocina": 80,
    "camarero": 18,
    "montaje": 60,
    "transporte": 120,
    "responsable_evento": 250,
}


def calcular_personal_evento(evento, menu=None, tipo_servicio="catering", complejidad="media"):
    personas = int(evento.get("personas") or 0)
    if personas <= 0:
        return {"ok": False, "error": "El evento no tiene numero de personas", "personal": {}}

    multiplicador = {"baja": 0.85, "media": 1.0, "alta": 1.25}.get(str(complejidad).lower(), 1.0)
    servicio = str(tipo_servicio or evento.get("tipo") or "catering").lower()

    ratios = dict(RATIOS_BASE)
    if "buffet" in servicio:
        ratios["camarero"] = 25
    if "boda" in servicio or "banquete" in servicio:
        ratios["camarero"] = 16
        ratios["montaje"] = 50
    if menu and len(menu.get("platos", [])) >= 5:
        multiplicador += 0.15

    personal = {}
    for rol, ratio in ratios.items():
        cantidad = max(1, ceil((personas / ratio) * multiplicador))
        if rol == "responsable_evento" and personas < 80:
            cantidad = 1
        personal[rol] = cantidad

    horas_estimadas = estimar_horas_personal(personal, personas, servicio)
    return {
        "ok": True,
        "id_evento": evento.get("id_evento"),
        "personas": personas,
        "tipo_servicio": servicio,
        "complejidad": complejidad,
        "personal": personal,
        "horas_estimadas": horas_estimadas,
        "total_personas_equipo": sum(personal.values()),
    }


def estimar_horas_personal(personal, personas=0, tipo_servicio="catering"):
    horas_base = 6
    if "boda" in str(tipo_servicio).lower() or "banquete" in str(tipo_servicio).lower():
        horas_base = 8
    if int(personas or 0) >= 150:
        horas_base += 1
    return {rol: cantidad * horas_base for rol, cantidad in personal.items()}


def resumen_personal_evento(plan):
    if not plan.get("ok"):
        return "No se pudo calcular el personal del evento."
    lineas = ["PERSONAL EVENTO", f"Personas evento: {plan.get('personas')}"]
    for rol, cantidad in plan.get("personal", {}).items():
        lineas.append(f"- {rol}: {cantidad}")
    lineas.append(f"Total equipo: {plan.get('total_personas_equipo')}")
    return "\n".join(lineas)
