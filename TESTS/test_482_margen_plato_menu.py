import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from SERVICIOS.margen_plato_menu_482 import calcular_margen_plato, calcular_margen_menu, calcular_margen_evento


def main():
    receta = {"nombre": "Paella", "raciones": 1, "precio_venta": 20, "ingredientes": [{"articulo": "Arroz", "cantidad": 0.1}, {"articulo": "Gamba", "cantidad": 0.1}]}
    precios = {"Arroz": 2, "Gamba": 10}
    margen = calcular_margen_plato(receta, precios_actuales=precios)
    assert margen["coste_racion"] == 1.2
    assert margen["margen"] == 18.8
    menu = calcular_margen_menu("Menu", [receta], precios_actuales=precios)
    assert menu["coste_total"] == 1.2
    evento = calcular_margen_evento({"nombre": "Evento", "personas": 10, "presupuesto": 500}, [{"coste_total": 200}])
    assert evento["margen_total"] == 300
    print("TEST OK 4.8.2 Margen plato/menu")


if __name__ == "__main__":
    main()
