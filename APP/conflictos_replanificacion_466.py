from SERVICIOS.conflictos_replanificacion_466 import detectar_conflictos_produccion, replanificar_basico


def main():
    tareas = [
        {"id": "t1", "nombre": "Fondo", "inicio": "2026-07-09T08:00", "fin": "2026-07-09T09:00", "recurso": "horno", "cocinero": "Ana"},
        {"id": "t2", "nombre": "Pollo", "inicio": "2026-07-09T08:30", "fin": "2026-07-09T09:15", "recurso": "horno", "cocinero": "Ana"},
    ]
    print("Conflictos:", detectar_conflictos_produccion(tareas))
    print("Replanificación:", replanificar_basico(tareas)["ok"])


if __name__ == "__main__":
    main()
