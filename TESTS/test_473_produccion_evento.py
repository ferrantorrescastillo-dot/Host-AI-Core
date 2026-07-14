import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from SERVICIOS.gestion_eventos_471 import crear_evento
from SERVICIOS.menus_evento_472 import crear_menu_evento, asignar_menu_evento
from SERVICIOS.produccion_evento_473 import generar_produccion_evento, integrar_produccion_evento, resumen_produccion_evento


def main():
    evento = crear_evento("Boda", "2026-08-03", "14:00", personas=120, estado="confirmado")
    menu = crear_menu_evento("Menu", [
        {"nombre": "Fondo", "coste_persona": 2, "minutos_activos": 45, "minutos_pasivos": 300, "dias_previos": 1},
        {"nombre": "Paella", "coste_persona": 10, "minutos_activos": 90, "minutos_pasivos": 15},
    ], precio_venta_persona=50)
    evento = asignar_menu_evento(evento, menu)
    plan = generar_produccion_evento(evento, menu)
    assert plan["total_tareas"] == 2
    assert plan["tareas"][0]["prioridad"] in ("alta", "media")
    evento2 = integrar_produccion_evento(evento, plan)
    assert len(evento2["produccion"]) == 2
    assert resumen_produccion_evento(plan)["minutos_activos"] == 135
    print("TEST OK 4.7.3 Produccion evento")


if __name__ == "__main__":
    main()
