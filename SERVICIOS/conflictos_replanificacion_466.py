# Host AI 4.6.6 - Conflictos de producción y replanificación

from datetime import datetime, timedelta

try:
    from SERVICIOS.recursos_cocina_465 import detectar_conflictos_recursos
except Exception:
    from recursos_cocina_465 import detectar_conflictos_recursos


def _dt(valor):
    if isinstance(valor, datetime):
        return valor
    return datetime.fromisoformat(str(valor))


def _minutos(tarea):
    inicio = _dt(tarea["inicio"])
    fin = _dt(tarea["fin"])
    return int((fin - inicio).total_seconds() // 60)


def detectar_conflictos_produccion(tareas, recursos=None):
    conflictos = []

    # Recursos compartidos
    conflictos.extend(detectar_conflictos_recursos(tareas, recursos))

    # Cocinero doblemente asignado
    por_cocinero = {}
    for tarea in tareas:
        cocinero = tarea.get("cocinero")
        if cocinero:
            por_cocinero.setdefault(cocinero, []).append(tarea)

    for cocinero, lista in por_cocinero.items():
        lista = sorted(lista, key=lambda t: _dt(t["inicio"]))
        for actual, siguiente in zip(lista, lista[1:]):
            if _dt(actual["fin"]) > _dt(siguiente["inicio"]):
                conflictos.append({
                    "tipo": "cocinero_solapado",
                    "cocinero": cocinero,
                    "tareas": [actual.get("nombre"), siguiente.get("nombre")],
                    "momento": _dt(siguiente["inicio"]).isoformat(timespec="minutes"),
                })

    # Dependencias no respetadas
    fin_por_id = {t.get("id"): _dt(t["fin"]) for t in tareas if t.get("id")}
    for tarea in tareas:
        for dep in tarea.get("depende_de", []) or []:
            if dep in fin_por_id and fin_por_id[dep] > _dt(tarea["inicio"]):
                conflictos.append({
                    "tipo": "dependencia_no_respetada",
                    "tarea": tarea.get("nombre"),
                    "depende_de": dep,
                    "inicio_tarea": _dt(tarea["inicio"]).isoformat(timespec="minutes"),
                    "fin_dependencia": fin_por_id[dep].isoformat(timespec="minutes"),
                })

    return conflictos


def replanificar_basico(tareas, recursos=None, margen_minutos=5):
    """Replanifica de forma conservadora desplazando tareas conflictivas hacia adelante."""
    tareas = [dict(t) for t in tareas]
    tareas.sort(key=lambda t: _dt(t["inicio"]))

    for _ in range(20):
        conflictos = detectar_conflictos_produccion(tareas, recursos)
        if not conflictos:
            return {"ok": True, "tareas": tareas, "conflictos_resueltos": True, "conflictos": []}

        conflicto = conflictos[0]
        nombres = conflicto.get("tareas") or [conflicto.get("tarea")]
        nombre_a_mover = nombres[-1] if nombres else None

        movida = False
        for tarea in tareas:
            if tarea.get("nombre") == nombre_a_mover:
                duracion = _minutos(tarea)
                nuevo_inicio = _dt(tarea["inicio"]) + timedelta(minutes=duracion + margen_minutos)
                tarea["inicio"] = nuevo_inicio.isoformat(timespec="minutes")
                tarea["fin"] = (nuevo_inicio + timedelta(minutes=duracion)).isoformat(timespec="minutes")
                tarea.setdefault("avisos", []).append("Replanificada automáticamente por conflicto")
                movida = True
                break
        if not movida:
            break

    return {"ok": False, "tareas": tareas, "conflictos_resueltos": False, "conflictos": detectar_conflictos_produccion(tareas, recursos)}
