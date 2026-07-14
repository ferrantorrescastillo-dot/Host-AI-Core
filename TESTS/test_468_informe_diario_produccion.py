from SERVICIOS.informe_diario_produccion_468 import generar_informe_diario_produccion, formatear_informe


def main():
    tareas = [
        {"id": "1", "nombre": "Croquetas", "estado": "terminada", "cocinero": "Ana", "minutos_activos": 45, "recurso": "fogones", "etiquetada": True},
        {"id": "2", "nombre": "Fondo", "estado": "terminada", "cocinero": "Marc", "minutos_activos": 30, "minutos_pasivos": 240, "recurso": "horno", "etiquetada": True},
    ]
    informe = generar_informe_diario_produccion(tareas, fecha="2026-07-09", documentos=["parte_produccion"])
    assert informe["total_tareas"] == 2
    assert informe["terminadas"] == 2
    assert informe["por_cocinero"]["Ana"]["minutos_activos"] == 45
    texto = formatear_informe(informe)
    assert "INFORME DIARIO" in texto
    print("TEST OK 4.6.8 Informe diario de producción")


if __name__ == "__main__":
    main()
