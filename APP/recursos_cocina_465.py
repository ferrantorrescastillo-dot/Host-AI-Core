from SERVICIOS.recursos_cocina_465 import reservar_recursos, resumen_recursos


def main():
    tareas = [
        {"id": "t1", "nombre": "Asar pollo", "inicio": "2026-07-09T08:00", "fin": "2026-07-09T08:45", "recurso": "horno"},
        {"id": "t2", "nombre": "Cocer arroz", "inicio": "2026-07-09T08:10", "fin": "2026-07-09T08:40", "recurso": "fogones"},
    ]
    resultado = reservar_recursos(tareas)
    print("RECURSOS OK:", resultado["ok"])
    print(resumen_recursos(tareas))


if __name__ == "__main__":
    main()
