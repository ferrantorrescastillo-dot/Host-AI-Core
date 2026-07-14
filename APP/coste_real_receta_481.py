# APP Host AI 4.8.1 - Coste real por receta

from SERVICIOS.coste_real_receta_481 import calcular_coste_real_receta


def main():
    receta = {
        "nombre": "Paella marisco",
        "raciones": 10,
        "ingredientes": [
            {"articulo": "Arroz bomba", "cantidad": 1, "unidad": "kg", "merma_pct": 2},
            {"articulo": "Gambon", "cantidad": 0.8, "unidad": "kg", "merma_pct": 5},
        ],
    }
    precios = {"Arroz bomba": 2.4, "Gambon": 13.0}
    print("=== HOST AI 4.8.1 - COSTE REAL RECETA ===")
    print(calcular_coste_real_receta(receta, precios))


if __name__ == "__main__":
    main()
