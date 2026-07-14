import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from SERVICIOS.rentabilidad_carta_483 import analizar_rentabilidad_carta, ranking_rentabilidad, recomendaciones_carta


def main():
    platos = [
        {"nombre": "Paella", "raciones": 1, "precio_venta": 20, "ingredientes": [{"articulo": "Arroz", "cantidad": 0.1}]},
        {"nombre": "Tapa cara", "raciones": 1, "precio_venta": 4, "ingredientes": [{"articulo": "Producto caro", "cantidad": 1}]},
    ]
    precios = {"Arroz": 2, "Producto caro": 3}
    analisis = analizar_rentabilidad_carta(platos, precios_actuales=precios, ventas={"Paella": 50, "Tapa cara": 30})
    assert analisis["total_platos"] == 2
    assert len(analisis["criticos"]) >= 1
    ranking = ranking_rentabilidad(analisis)
    assert ranking["mejores"]
    assert recomendaciones_carta(analisis)
    print("TEST OK 4.8.3 Rentabilidad carta")


if __name__ == "__main__":
    main()
