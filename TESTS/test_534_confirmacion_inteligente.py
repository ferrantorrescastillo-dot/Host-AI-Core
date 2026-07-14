from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento
from SERVICIOS.confirmacion_inteligente_534 import analizar_confirmaciones_flujo, interpretar_confirmacion


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
    resultado = analizar_confirmaciones_flujo(flujo)
    assert resultado["ok"] is True
    assert resultado["requiere_confirmacion_global"] is True
    assert resultado["acciones_con_confirmacion"]
    assert resultado["acciones_criticas"]
    assert interpretar_confirmacion("S")["tipo"] == "confirmar_todo"
    assert interpretar_confirmacion("sí, adelante")["tipo"] == "confirmar_todo"
    assert interpretar_confirmacion("no")["tipo"] == "cancelar"
    assert interpretar_confirmacion("seleccionar")["tipo"] == "seleccionar"
    print("TEST OK 5.3.4 Confirmación inteligente")


if __name__ == "__main__":
    main()
