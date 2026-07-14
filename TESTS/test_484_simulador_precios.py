import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from SERVICIOS.simulador_precios_484 import simular_precio_plato, simular_subida_porcentual, precio_objetivo_por_margen


def main():
    receta = {"nombre": "Paella", "raciones": 1, "precio_venta": 20, "ingredientes": [{"articulo": "Arroz", "cantidad": 0.1}]}
    precios = {"Arroz": 2}
    sim = simular_precio_plato(receta, [20, 22], precios_actuales=precios, ventas_estimadas=100)
    assert sim["mejor_opcion"]["precio_venta"] == 22
    subida = simular_subida_porcentual(receta, 10, precios_actuales=precios, ventas_estimadas=100)
    assert subida["precio_nuevo"] == 22
    objetivo = precio_objetivo_por_margen(receta, 0.8, precios_actuales=precios)
    assert objetivo["precio_recomendado"] == 1.0
    print("TEST OK 4.8.4 Simulador precios")


if __name__ == "__main__":
    main()
