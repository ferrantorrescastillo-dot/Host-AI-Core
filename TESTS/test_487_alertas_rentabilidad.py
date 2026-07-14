from SERVICIOS.alertas_rentabilidad_487 import evaluar_alerta_rentabilidad, generar_alertas_rentabilidad, resumen_alertas


def main():
    alerta = evaluar_alerta_rentabilidad({"nombre": "Canelón", "precio_venta": 9, "coste": 5}, margen_minimo=0.60)
    assert alerta["estado"] == "alerta"
    resultado = generar_alertas_rentabilidad([
        {"nombre": "Paella", "precio_venta": 45, "coste": 15},
        {"nombre": "Canelón", "precio_venta": 9, "coste": 5},
    ])
    assert resultado["total_items"] == 2
    assert resultado["total_alertas"] >= 1
    assert "alertas" in resumen_alertas(resultado).lower()
    print("TEST OK 4.8.7 Alertas de rentabilidad")


if __name__ == "__main__":
    main()
