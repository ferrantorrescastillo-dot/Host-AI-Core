import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from SERVICIOS.gestion_eventos_471 import crear_evento
from SERVICIOS.menus_evento_472 import crear_menu_evento
from SERVICIOS.compras_evento_474 import calcular_necesidades_evento, comparar_con_stock, generar_pedido_evento, integrar_compras_evento


def main():
    evento = crear_evento("Catering", "2026-08-04", personas=100)
    menu = crear_menu_evento("Menu", [
        {"nombre": "Paella", "coste_persona": 12, "ingredientes": [
            {"articulo": "Arroz bomba", "cantidad_persona": 0.1, "unidad": "kg", "proveedor": "Makro"},
            {"articulo": "Gambon", "cantidad_persona": 0.08, "unidad": "kg", "proveedor": "Pescados"},
        ]}
    ], precio_venta_persona=45)
    necesidades = calcular_necesidades_evento(evento, menu)
    assert len(necesidades) == 2
    comparacion = comparar_con_stock(necesidades, {"Arroz bomba": 4, "Gambon": 10})
    pedido = generar_pedido_evento(evento, comparacion)
    assert pedido["total_lineas"] == 1
    assert pedido["lineas"][0]["articulo"] == "Arroz bomba"
    evento2 = integrar_compras_evento(evento, pedido)
    assert len(evento2["compras"]) == 1
    print("TEST OK 4.7.4 Compras evento")


if __name__ == "__main__":
    main()
