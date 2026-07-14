from SERVICIOS.control_mermas_485 import registrar_merma, calcular_coste_mermas, generar_recomendaciones_mermas


def main():
    linea = registrar_merma("Tomate", 2, "kg", 2.5, "caducidad", "cuarto frio")
    assert linea["coste_total"] == 5.0
    resumen = calcular_coste_mermas([linea, {"articulo": "Arroz", "cantidad": 1, "coste_unitario": 1.8, "motivo": "sobreproduccion"}])
    assert resumen["numero_lineas"] == 2
    assert resumen["total_mermas"] == 6.8
    recs = generar_recomendaciones_mermas(resumen, umbral_alerta=5)
    assert recs
    print("TEST OK 4.8.5 Control de mermas")


if __name__ == "__main__":
    main()
