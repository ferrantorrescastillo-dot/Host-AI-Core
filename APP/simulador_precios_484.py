# APP Host AI 4.8.4 - Simulador de precios

from SERVICIOS.simulador_precios_484 import simular_precio_plato, simular_subida_porcentual, precio_objetivo_por_margen


def main():
    receta = {"nombre": "Paella", "raciones": 1, "precio_venta": 18, "ingredientes": [{"articulo": "Arroz", "cantidad": 0.1}, {"articulo": "Gamba", "cantidad": 0.08}]}
    precios = {"Arroz": 2.2, "Gamba": 14}
    print("=== HOST AI 4.8.4 - SIMULADOR PRECIOS ===")
    print(simular_precio_plato(receta, [18, 19, 20, 21], precios_actuales=precios, ventas_estimadas=100))
    print(simular_subida_porcentual(receta, 10, precios_actuales=precios, ventas_estimadas=100))
    print(precio_objetivo_por_margen(receta, 0.70, precios_actuales=precios))


if __name__ == "__main__":
    main()
