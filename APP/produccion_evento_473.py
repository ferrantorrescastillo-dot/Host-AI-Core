# APP Host AI 4.7.3 - Produccion automatica de evento

from SERVICIOS.gestion_eventos_471 import crear_evento
from SERVICIOS.menus_evento_472 import crear_menu_evento, asignar_menu_evento
from SERVICIOS.produccion_evento_473 import generar_produccion_evento, resumen_produccion_evento


def main():
    evento = crear_evento("Boda demo", "2026-07-25", "13:30", personas=150, estado="confirmado")
    menu = crear_menu_evento("Menu boda", [
        {"nombre": "Fondo oscuro", "coste_persona": 2.4, "minutos_activos": 60, "minutos_pasivos": 360, "dias_previos": 1},
        {"nombre": "Paella marisco", "coste_persona": 12, "minutos_activos": 90, "minutos_pasivos": 20},
    ], precio_venta_persona=55)
    evento = asignar_menu_evento(evento, menu)
    plan = generar_produccion_evento(evento, menu)
    print("=== HOST AI 4.7.3 - PRODUCCION EVENTO ===")
    print(resumen_produccion_evento(plan))
    for tarea in plan["tareas"]:
        print(tarea)


if __name__ == "__main__":
    main()
