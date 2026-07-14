from SERVICIOS.comparador_economico_proveedores_486 import comparar_proveedores, recomendacion_compra_proveedor


def main():
    ofertas = [
        {"proveedor": "A", "articulo": "Aceite", "precio_unitario": 5, "cantidad": 10, "transporte": 0, "fiabilidad": 0.98},
        {"proveedor": "B", "articulo": "Aceite", "precio_unitario": 4.8, "cantidad": 10, "transporte": 5, "fiabilidad": 0.92},
    ]
    resultado = comparar_proveedores(ofertas)
    assert resultado["numero_proveedores"] == 2
    assert resultado["mejor_opcion"]["proveedor"] in {"A", "B"}
    assert "Comprar" in recomendacion_compra_proveedor(ofertas)
    print("TEST OK 4.8.6 Comparador económico de proveedores")


if __name__ == "__main__":
    main()
