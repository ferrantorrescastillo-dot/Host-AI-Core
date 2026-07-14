from SERVICIOS.informe_diario_produccion_468 import generar_informe_diario_produccion, formatear_informe


def main():
    tareas = [
        {"id": "t1", "nombre": "Croquetas", "estado": "terminada", "cocinero": "Ana", "minutos_activos": 45, "etiquetada": True},
        {"id": "t2", "nombre": "Fondo", "estado": "pendiente", "cocinero": "Marc", "minutos_activos": 30, "minutos_pasivos": 240},
    ]
    informe = generar_informe_diario_produccion(tareas, fecha="2026-07-09")
    print(formatear_informe(informe))


if __name__ == "__main__":
    main()
