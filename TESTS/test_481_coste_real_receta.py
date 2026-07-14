import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from SERVICIOS.coste_real_receta_481 import calcular_coste_real_receta, calcular_costes_recetas


def main():
    receta = {"nombre": "Paella", "raciones": 10, "ingredientes": [
        {"articulo": "Arroz", "cantidad": 1, "unidad": "kg", "merma_pct": 0},
        {"articulo": "Gamba", "cantidad": 0.5, "unidad": "kg", "merma_pct": 10},
    ]}
    precios = {"Arroz": 2.0, "Gamba": 10.0}
    res = calcular_coste_real_receta(receta, precios)
    assert res["coste_total"] == 7.5
    assert res["coste_racion"] == 0.75
    lote = calcular_costes_recetas([receta], precios)
    assert lote["total_recetas"] == 1
    print("TEST OK 4.8.1 Coste real receta")


if __name__ == "__main__":
    main()
