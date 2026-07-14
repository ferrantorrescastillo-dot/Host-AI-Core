from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento, formatear_flujo_operativo


def main():
    datos = {
        "tipo": "boda",
        "personas": 180,
        "fecha": "sabado",
        "hora_servicio": "15:00",
        "menu": "menu boda",
        "lugar": "Mas Boronat",
        "restricciones": "sin restricciones",
        "objetivo": "flujo completo",
    }
    flujo = generar_flujo_operativo_evento(datos)
    print(formatear_flujo_operativo(flujo))


if __name__ == "__main__":
    main()
