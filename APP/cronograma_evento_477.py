# APP Host AI 4.7.7 - Cronograma evento

from SERVICIOS.cronograma_evento_477 import generar_cronograma_evento, formatear_cronograma


def main():
    evento = {"id_evento": "DEMO", "fecha": "2026-08-01", "hora": "13:30", "personas": 180}
    print(formatear_cronograma(generar_cronograma_evento(evento, produccion=["fondos", "aperitivos", "paella"])))


if __name__ == "__main__":
    main()
