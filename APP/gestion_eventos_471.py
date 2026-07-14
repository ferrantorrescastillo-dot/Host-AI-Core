# APP Host AI 4.7.1 - Gestion de eventos

from SERVICIOS.gestion_eventos_471 import crear_evento, validar_evento, guardar_evento


def main():
    evento = crear_evento(
        nombre="Evento demo Host AI",
        fecha="2026-07-20",
        hora="13:30",
        tipo="catering",
        personas=80,
        cliente="Cliente demo",
        lugar="Finca demo",
        observaciones="Prueba 4.7.1",
    )
    validacion = validar_evento(evento)
    print("=== HOST AI 4.7.1 - GESTION EVENTOS ===")
    print(validacion)
    if validacion["ok"]:
        print(guardar_evento(evento))


if __name__ == "__main__":
    main()
