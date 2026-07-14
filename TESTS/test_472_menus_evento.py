import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from SERVICIOS.gestion_eventos_471 import crear_evento
from SERVICIOS.menus_evento_472 import crear_menu_evento, calcular_menu_para_evento, asignar_menu_evento, comparar_menus_evento


def main():
    evento = crear_evento("Empresa", "2026-08-02", personas=100)
    menu = crear_menu_evento("Menu 45", [
        {"nombre": "Entrantes", "coste_persona": 6, "cantidad_persona": 1},
        {"nombre": "Paella", "coste_persona": 12, "cantidad_persona": 1},
    ], precio_venta_persona=45)
    resumen = calcular_menu_para_evento(menu, 100)
    assert resumen["venta_total"] == 4500
    assert resumen["coste_total"] == 1800
    evento = asignar_menu_evento(evento, menu)
    assert len(evento["menus"]) == 1
    comp = comparar_menus_evento([menu])
    assert comp["mejor_margen"]["nombre"] == "Menu 45"
    print("TEST OK 4.7.2 Menus evento")


if __name__ == "__main__":
    main()
