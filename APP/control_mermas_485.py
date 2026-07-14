from SERVICIOS.control_mermas_485 import calcular_coste_mermas, generar_recomendaciones_mermas


def main():
    mermas = [
        {"articulo": "Tomate", "cantidad": 2, "unidad": "kg", "coste_unitario": 2.5, "motivo": "caducidad", "area": "cuarto frio"},
        {"articulo": "Arroz", "cantidad": 1, "unidad": "kg", "coste_unitario": 1.8, "motivo": "sobreproduccion", "area": "cocina"},
    ]
    resumen = calcular_coste_mermas(mermas)
    print("TOTAL MERMAS:", resumen["total_mermas"], "€")
    for rec in generar_recomendaciones_mermas(resumen):
        print("-", rec)


if __name__ == "__main__":
    main()
