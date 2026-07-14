from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento


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
    assert flujo["ok"] is True
    assert flujo["estado"] == "flujo_generado"
    assert len(flujo["pasos"]) >= 6
    assert flujo["modifica_datos_directamente"] is False

    incompleto = generar_flujo_operativo_evento({"tipo": "boda", "personas": 180})
    assert incompleto["ok"] is False
    assert "fecha" in incompleto["faltan"]
    print("TEST OK 5.3.1 Generador flujo operativo")


if __name__ == "__main__":
    main()
