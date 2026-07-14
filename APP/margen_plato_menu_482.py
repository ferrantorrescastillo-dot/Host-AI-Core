# APP Host AI 4.8.2 - Margen plato/menu

from SERVICIOS.margen_plato_menu_482 import calcular_margen_plato, calcular_margen_menu


def main():
    receta = {
        "nombre": "Paella marisco",
        "raciones": 1,
        "precio_venta": 18,
        "ingredientes": [
            {"articulo": "Arroz bomba", "cantidad": 0.1, "unidad": "kg"},
            {"articulo": "Gambon", "cantidad": 0.08, "unidad": "kg"},
        ],
    }
    precios = {"Arroz bomba": 2.4, "Gambon": 13.0}
    print("=== HOST AI 4.8.2 - MARGEN PLATO/MENU ===")
    print(calcular_margen_plato(receta, precios_actuales=precios))
    print(calcular_margen_menu("Menu demo", [receta], precios_actuales=precios))


if __name__ == "__main__":
    main()
