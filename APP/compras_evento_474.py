# APP Host AI 4.7.4 - Compras automaticas de evento

from SERVICIOS.gestion_eventos_471 import crear_evento
from SERVICIOS.menus_evento_472 import crear_menu_evento
from SERVICIOS.compras_evento_474 import calcular_necesidades_evento, comparar_con_stock, generar_pedido_evento


def main():
    evento = crear_evento("Catering empresa", "2026-07-30", "14:00", personas=100)
    menu = crear_menu_evento("Menu empresa", [
        {"nombre": "Paella", "ingredientes": [
            {"articulo": "Arroz bomba", "cantidad_persona": 0.1, "unidad": "kg", "proveedor": "Makro"},
            {"articulo": "Gambon", "cantidad_persona": 0.08, "unidad": "kg", "proveedor": "Proveedor pescado"},
        ], "coste_persona": 9.5}
    ], precio_venta_persona=35)
    necesidades = calcular_necesidades_evento(evento, menu)
    comparacion = comparar_con_stock(necesidades, {"Arroz bomba": 4})
    pedido = generar_pedido_evento(evento, comparacion)
    print("=== HOST AI 4.7.4 - COMPRAS EVENTO ===")
    print(pedido)


if __name__ == "__main__":
    main()
