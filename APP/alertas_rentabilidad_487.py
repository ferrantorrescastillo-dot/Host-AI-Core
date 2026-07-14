from SERVICIOS.alertas_rentabilidad_487 import generar_alertas_rentabilidad, resumen_alertas


def main():
    platos = [
        {"nombre": "Paella marisco", "precio_venta": 45, "coste": 16},
        {"nombre": "Canelón", "precio_venta": 9, "coste": 5},
    ]
    alertas = generar_alertas_rentabilidad(platos)
    print(resumen_alertas(alertas))


if __name__ == "__main__":
    main()
