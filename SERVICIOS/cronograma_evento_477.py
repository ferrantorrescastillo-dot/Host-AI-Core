# Host AI 4.7.7 - Cronograma completo de evento

from datetime import datetime, timedelta


def _parse_fecha_hora(evento):
    fecha = evento.get("fecha") or datetime.now().date().isoformat()
    hora = evento.get("hora") or "13:00"
    return datetime.fromisoformat(f"{fecha}T{hora[:5]}")


def generar_cronograma_evento(evento, produccion=None, personal=None, material=None):
    servicio = _parse_fecha_hora(evento)
    personas = int(evento.get("personas") or 0)
    produccion = produccion or []
    tareas = []

    def add(inicio, titulo, area="evento", duracion_min=60, responsable=None):
        tareas.append({
            "inicio": inicio.strftime("%Y-%m-%d %H:%M"),
            "fin": (inicio + timedelta(minutes=duracion_min)).strftime("%Y-%m-%d %H:%M"),
            "titulo": titulo,
            "area": area,
            "responsable": responsable or area,
            "duracion_min": duracion_min,
        })

    add(servicio - timedelta(days=2, hours=2), "Revisar pedido, stock y necesidades finales", "compras", 45, "responsable_evento")
    add(servicio - timedelta(days=1, hours=5), "Produccion principal del evento", "cocina", max(120, len(produccion) * 35), "jefe_cocina")
    add(servicio - timedelta(days=1, hours=1), "Preparar material, etiquetar y organizar carga", "almacen", 90, "montaje")
    add(servicio - timedelta(hours=5), "Carga de vehiculo y comprobacion checklist", "logistica", 60, "transporte")
    add(servicio - timedelta(hours=3), "Salida hacia evento", "transporte", 60, "transporte")
    add(servicio - timedelta(hours=2), "Montaje cocina, sala y pase", "montaje", 90, "responsable_evento")
    add(servicio - timedelta(minutes=30), "Briefing final antes del servicio", "equipo", 20, "responsable_evento")
    add(servicio, "Inicio del servicio", "servicio", max(90, personas // 2), "responsable_evento")
    add(servicio + timedelta(hours=3), "Recogida, limpieza y devolucion material", "cierre", 120, "montaje")

    tareas.sort(key=lambda x: x["inicio"])
    return {"ok": True, "id_evento": evento.get("id_evento"), "servicio": servicio.strftime("%Y-%m-%d %H:%M"), "tareas": tareas, "total_tareas": len(tareas)}


def agrupar_cronograma_por_dia(cronograma):
    dias = {}
    for tarea in cronograma.get("tareas", []):
        dia = tarea["inicio"][:10]
        dias.setdefault(dia, []).append(tarea)
    return dias


def formatear_cronograma(cronograma):
    if not cronograma.get("ok"):
        return "No se pudo generar cronograma."
    lineas = ["CRONOGRAMA EVENTO", f"Servicio: {cronograma.get('servicio')}"]
    for dia, tareas in agrupar_cronograma_por_dia(cronograma).items():
        lineas.append("")
        lineas.append(dia)
        for tarea in tareas:
            lineas.append(f"- {tarea['inicio'][11:16]} {tarea['titulo']} ({tarea['area']})")
    return "\n".join(lineas)
