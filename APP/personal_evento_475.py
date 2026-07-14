# APP Host AI 4.7.5 - Personal evento

from SERVICIOS.personal_evento_475 import calcular_personal_evento, resumen_personal_evento


def main():
    evento = {"id_evento": "DEMO", "nombre": "Boda demo", "personas": 180, "tipo": "boda"}
    plan = calcular_personal_evento(evento, tipo_servicio="boda", complejidad="alta")
    print(resumen_personal_evento(plan))


if __name__ == "__main__":
    main()
