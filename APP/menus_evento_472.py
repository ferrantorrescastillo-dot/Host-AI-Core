# APP Host AI 4.7.2 - Menus de evento

from SERVICIOS.menus_evento_472 import crear_menu_evento, calcular_menu_para_evento


def main():
    menu = crear_menu_evento("Menu paella premium", [
        {"nombre": "Aperitivos", "coste_persona": 6.5, "cantidad_persona": 1, "unidad": "pack"},
        {"nombre": "Paella marisco", "coste_persona": 11.8, "cantidad_persona": 1, "unidad": "racion"},
        {"nombre": "Postre", "coste_persona": 3.2, "cantidad_persona": 1, "unidad": "u"},
    ], precio_venta_persona=45)
    print("=== HOST AI 4.7.2 - MENU EVENTO ===")
    print(menu)
    print(calcular_menu_para_evento(menu, 120))


if __name__ == "__main__":
    main()
