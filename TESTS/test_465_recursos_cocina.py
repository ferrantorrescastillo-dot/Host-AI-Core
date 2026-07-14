from SERVICIOS.recursos_cocina_465 import detectar_conflictos_recursos, reservar_recursos, resumen_recursos


def main():
    tareas = [
        {"id": "1", "nombre": "Pollo", "inicio": "2026-07-09T08:00", "fin": "2026-07-09T09:00", "recurso": "horno"},
        {"id": "2", "nombre": "Verduras", "inicio": "2026-07-09T08:15", "fin": "2026-07-09T08:45", "recurso": "horno"},
        {"id": "3", "nombre": "Arroz", "inicio": "2026-07-09T08:15", "fin": "2026-07-09T08:45", "recurso": "fogones"},
    ]
    conflictos = detectar_conflictos_recursos(tareas, {"horno": 1, "fogones": 4})
    assert len(conflictos) == 1
    assert conflictos[0]["recurso"] == "horno"
    assert reservar_recursos(tareas, {"horno": 2})["ok"] is True
    assert resumen_recursos(tareas)["horno"]["usos"] == 2
    print("TEST OK 4.6.5 Recursos de cocina")


if __name__ == "__main__":
    main()
