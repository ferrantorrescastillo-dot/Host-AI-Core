from SERVICIOS.recomendaciones_inteligentes_496 import analizar_recomendaciones, formatear_recomendaciones


def main():
    datos = {
        "stock": [{"nombre": "Gambón", "stock_actual": 1, "stock_minimo": 5}],
        "compras": [{"nombre": "Aceite oliva", "variacion_precio": 0.18}],
        "produccion": [{"nombre": "Croquetas", "merma": 0.12}],
        "rentabilidad": [{"nombre": "Paella mixta", "margen": 0.22, "ventas": 40}],
    }
    print(formatear_recomendaciones(analizar_recomendaciones(datos)))


if __name__ == "__main__":
    main()
