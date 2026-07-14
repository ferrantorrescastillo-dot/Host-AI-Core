from SERVICIOS.recomendaciones_inteligentes_496 import analizar_recomendaciones, formatear_recomendaciones


def main():
    resultado = analizar_recomendaciones({
        "stock": [
            {"nombre": "Gambón", "stock_actual": 1, "stock_minimo": 5},
            {"nombre": "Harina", "stock_actual": 50, "stock_minimo": 10, "rotacion": 0},
        ],
        "compras": [{"nombre": "Aceite", "variacion_precio": 0.22}],
        "produccion": [{"nombre": "Croquetas", "retraso_minutos": 45, "merma": 0.10}],
        "rentabilidad": [{"nombre": "Paella", "margen": 0.21, "ventas": 40}],
    })
    assert resultado["total_recomendaciones"] >= 5
    assert resultado["prioritarias"]
    texto = formatear_recomendaciones(resultado)
    assert "RECOMENDACIONES INTELIGENTES" in texto
    assert "Paella" in texto or "Gambón" in texto
    print("TEST OK 4.9.6 Recomendaciones inteligentes")


if __name__ == "__main__":
    main()
