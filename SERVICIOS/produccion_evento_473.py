# Host AI 4.7.3 - Produccion automatica del evento

from datetime import datetime, timedelta


try:
    from SERVICIOS.menus_evento_472 import calcular_menu_para_evento
except Exception:
    from menus_evento_472 import calcular_menu_para_evento


def _parse_fecha_hora(fecha, hora=None):
    texto = f"{fecha} {hora or '13:00'}".strip()
    for fmt in ("%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(texto, fmt)
        except Exception:
            pass
    return datetime.now().replace(hour=13, minute=0, second=0, microsecond=0)


def generar_produccion_evento(evento, menu=None, recetas=None):
    menu = menu or (evento.get("menus") or [{}])[0]
    resumen_menu = calcular_menu_para_evento(menu, evento.get("personas", 0)) if menu else {"platos": []}
    recetas = recetas or {}
    servicio = _parse_fecha_hora(evento.get("fecha"), evento.get("hora"))
    tareas = []
    for plato in resumen_menu.get("platos", []):
        nombre = plato.get("nombre") or plato.get("receta") or "Elaboracion"
        receta = recetas.get(nombre, {}) if isinstance(recetas, dict) else {}
        minutos_activos = int(receta.get("minutos_activos", plato.get("minutos_activos", 30)) or 30)
        minutos_pasivos = int(receta.get("minutos_pasivos", plato.get("minutos_pasivos", 0)) or 0)
        dias_previos = int(receta.get("dias_previos", plato.get("dias_previos", 1 if minutos_pasivos >= 120 else 0)) or 0)
        inicio_recomendado = servicio - timedelta(days=dias_previos, minutes=minutos_activos + minutos_pasivos + 60)
        tareas.append({
            "evento": evento.get("id_evento"),
            "elaboracion": nombre,
            "cantidad_total": plato.get("cantidad_total"),
            "unidad": plato.get("unidad", "u"),
            "minutos_activos": minutos_activos,
            "minutos_pasivos": minutos_pasivos,
            "inicio_recomendado": inicio_recomendado.strftime("%Y-%m-%d %H:%M"),
            "servicio": servicio.strftime("%Y-%m-%d %H:%M"),
            "estado": "pendiente",
            "prioridad": "alta" if dias_previos or minutos_pasivos >= 120 else "media",
        })
    tareas.sort(key=lambda t: (t["inicio_recomendado"], 0 if t["prioridad"] == "alta" else 1))
    return {
        "id_evento": evento.get("id_evento"),
        "nombre_evento": evento.get("nombre"),
        "servicio": servicio.strftime("%Y-%m-%d %H:%M"),
        "total_tareas": len(tareas),
        "tareas": tareas,
    }


def integrar_produccion_evento(evento, plan_produccion):
    copia = dict(evento)
    copia["produccion"] = plan_produccion.get("tareas", [])
    copia["estado"] = "en_produccion" if copia.get("estado") == "confirmado" else copia.get("estado", "borrador")
    return copia


def resumen_produccion_evento(plan):
    activos = sum(int(t.get("minutos_activos", 0)) for t in plan.get("tareas", []))
    pasivos = sum(int(t.get("minutos_pasivos", 0)) for t in plan.get("tareas", []))
    return {
        "total_tareas": plan.get("total_tareas", len(plan.get("tareas", []))),
        "minutos_activos": activos,
        "minutos_pasivos": pasivos,
        "resumen": f"{plan.get('total_tareas', 0)} tareas, {activos} min activos, {pasivos} min pasivos",
    }
