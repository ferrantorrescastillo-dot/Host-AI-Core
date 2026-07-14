# APP Host AI 4.8.3 - Rentabilidad de carta

from SERVICIOS.rentabilidad_carta_483 import analizar_rentabilidad_carta, recomendaciones_carta


def main():
    platos = [
        {"nombre": "Paella", "raciones": 1, "precio_venta": 18, "ingredientes": [{"articulo": "Arroz", "cantidad": 0.1}, {"articulo": "Gamba", "cantidad": 0.08}]},
        {"nombre": "Croquetas", "raciones": 1, "precio_venta": 9, "ingredientes": [{"articulo": "Harina", "cantidad": 0.05}, {"articulo": "Leche", "cantidad": 0.2}]},
    ]
    precios = {"Arroz": 2.2, "Gamba": 14, "Harina": 1.1, "Leche": 0.9}
    ventas = {"Paella": 80, "Croquetas": 30}
    analisis = analizar_rentabilidad_carta(platos, precios_actuales=precios, ventas=ventas)
    print("=== HOST AI 4.8.3 - RENTABILIDAD CARTA ===")
    print(analisis)
    print(recomendaciones_carta(analisis))


if __name__ == "__main__":
    main()
