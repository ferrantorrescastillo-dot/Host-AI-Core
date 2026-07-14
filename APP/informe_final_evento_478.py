# APP Host AI 4.7.8 - Informe final evento

from SERVICIOS.informe_final_evento_478 import calcular_resultado_evento, formatear_informe_final_evento


def main():
    evento = {"id_evento": "DEMO", "nombre": "Boda demo", "personas": 180, "presupuesto": 8100}
    costes = {"materia_prima": 2400, "personal": 1700, "transporte": 350, "material": 450}
    print(formatear_informe_final_evento(calcular_resultado_evento(evento, costes)))


if __name__ == "__main__":
    main()
