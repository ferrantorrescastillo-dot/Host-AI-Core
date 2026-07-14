# Host AI 4.6.5 - Recursos de cocina
# Gestiona disponibilidad y conflictos de recursos: horno, abatidor, brasa, fogones, etc.

from datetime import datetime, timedelta


def _dt(valor):
    if isinstance(valor, datetime):
        return valor
    return datetime.fromisoformat(str(valor))


def _solapan(inicio_a, fin_a, inicio_b, fin_b):
    return max(inicio_a, inicio_b) < min(fin_a, fin_b)


RECURSOS_DEFECTO = {
    "horno": {"capacidad": 1, "nombre": "Horno"},
    "abatidor": {"capacidad": 1, "nombre": "Abatidor"},
    "brasa": {"capacidad": 1, "nombre": "Brasa"},
    "fogones": {"capacidad": 4, "nombre": "Fogones"},
    "freidora": {"capacidad": 1, "nombre": "Freidora"},
}


def normalizar_recursos(recursos=None):
    base = dict(RECURSOS_DEFECTO)
    if recursos:
        for clave, valor in recursos.items():
            if isinstance(valor, dict):
                base[clave] = {**base.get(clave, {}), **valor}
            else:
                base[clave] = {"capacidad": int(valor), "nombre": clave.title()}
    return base


def detectar_conflictos_recursos(tareas, recursos=None):
    """Devuelve conflictos cuando un recurso supera su capacidad en una franja horaria."""
    recursos = normalizar_recursos(recursos)
    conflictos = []
    tareas_recurso = {}

    for tarea in tareas:
        recurso = tarea.get("recurso") or tarea.get("recurso_principal")
        if not recurso:
            continue
        tareas_recurso.setdefault(recurso, []).append(tarea)

    for recurso, lista in tareas_recurso.items():
        capacidad = int(recursos.get(recurso, {}).get("capacidad", 1))
        eventos = []
        for tarea in lista:
            eventos.append((_dt(tarea["inicio"]), 1, tarea))
            eventos.append((_dt(tarea["fin"]), -1, tarea))
        eventos.sort(key=lambda x: (x[0], x[1]))

        activas = []
        for momento, tipo, tarea in eventos:
            if tipo == -1:
                activas = [t for t in activas if t.get("id") != tarea.get("id")]
            else:
                activas.append(tarea)
                if len(activas) > capacidad:
                    conflictos.append({
                        "recurso": recurso,
                        "momento": momento.isoformat(timespec="minutes"),
                        "capacidad": capacidad,
                        "uso": len(activas),
                        "tareas": [t.get("nombre", t.get("id", "tarea")) for t in activas],
                        "tipo": "sobrecarga_recurso",
                    })
    return conflictos


def reservar_recursos(tareas, recursos=None):
    conflictos = detectar_conflictos_recursos(tareas, recursos)
    return {
        "ok": len(conflictos) == 0,
        "conflictos": conflictos,
        "tareas": tareas,
        "recursos": normalizar_recursos(recursos),
    }


def resumen_recursos(tareas, recursos=None):
    recursos = normalizar_recursos(recursos)
    resumen = {clave: {"capacidad": datos.get("capacidad", 1), "usos": 0} for clave, datos in recursos.items()}
    for tarea in tareas:
        recurso = tarea.get("recurso") or tarea.get("recurso_principal")
        if recurso:
            resumen.setdefault(recurso, {"capacidad": 1, "usos": 0})
            resumen[recurso]["usos"] += 1
    return resumen
