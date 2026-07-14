from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento
from SERVICIOS.ejecutor_flujo_operativo_532 import ejecutar_flujo_operativo


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
    resultado = ejecutar_flujo_operativo(flujo, confirmar=True)
    assert resultado["ok"] is True
    assert resultado["estado"] == "ejecutado_modo_seguro"
    assert resultado["modifico_datos_reales"] is False
    assert len(resultado["resultados"]) == len(flujo["pasos"])
    assert resultado["pendientes_confirmacion"]
    print("TEST OK 5.3.2 Ejecutor flujo operativo")


if __name__ == "__main__":
    main()
