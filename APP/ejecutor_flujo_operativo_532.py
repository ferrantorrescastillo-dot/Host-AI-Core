from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento, formatear_flujo_operativo
from SERVICIOS.ejecutor_flujo_operativo_532 import ejecutar_flujo_operativo, formatear_ejecucion_flujo


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
    print("\n" + "=" * 60 + "\n")
    resultado = ejecutar_flujo_operativo(flujo, confirmar=True)
    print(formatear_ejecucion_flujo(resultado))


if __name__ == "__main__":
    main()
