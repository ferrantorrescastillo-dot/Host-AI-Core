from SERVICIOS.comparador_economico_proveedores_486 import comparar_proveedores, recomendacion_compra_proveedor


def main():
    ofertas = [
        {"proveedor": "Makro", "articulo": "Arroz bomba", "precio_unitario": 2.20, "cantidad": 10, "transporte": 0, "fiabilidad": 0.98},
        {"proveedor": "Proveedor Local", "articulo": "Arroz bomba", "precio_unitario": 2.05, "cantidad": 10, "transporte": 3, "fiabilidad": 0.90},
    ]
    print(recomendacion_compra_proveedor(ofertas))
    print(comparar_proveedores(ofertas))


if __name__ == "__main__":
    main()
