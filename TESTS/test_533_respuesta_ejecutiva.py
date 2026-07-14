from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento
from SERVICIOS.ejecutor_flujo_operativo_532 import ejecutar_flujo_operativo
from SERVICIOS.respuesta_ejecutiva_533 import generar_respuesta_ejecutiva_evento


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
    ejecucion = ejecutar_flujo_operativo(flujo)
    respuesta = generar_respuesta_ejecutiva_evento(flujo, ejecucion)
    assert respuesta["ok"] is True
    assert respuesta["estado"] == "respuesta_ejecutiva_generada"
    mensaje = respuesta["mensaje"].lower()
    assert "resumen del evento" in mensaje
    assert "producción" in mensaje or "produccion" in mensaje
    assert "stock" in mensaje
    assert "compras" in mensaje
    assert "no se han modificado datos reales" in mensaje
    print("TEST OK 5.3.3 Respuesta ejecutiva")


if __name__ == "__main__":
    main()
