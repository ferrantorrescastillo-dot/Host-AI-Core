from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento
from SERVICIOS.planificador_inteligente_535 import detectar_dependencias_pendientes, planificar_ejecucion_inteligente


def test_planificador_flujo_completo():
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
    plan = planificar_ejecucion_inteligente(flujo)
    assert plan["ok"] is True
    assert plan["estado"] == "planificado"
    codigos = [p["codigo"] for p in plan["plan"]]
    assert codigos[0] == "EVENTO_CREAR"
    assert codigos.index("STOCK_REVISAR") < codigos.index("COMPRAS_PREPARAR")
    assert plan["total_pasos"] >= 8


def test_planificador_detecta_dependencia_faltante():
    pasos = [{"codigo": "COMPRAS_PREPARAR", "nombre": "Compras"}]
    pendientes = detectar_dependencias_pendientes(pasos)
    assert "COMPRAS_PREPARAR" in pendientes
    assert "STOCK_REVISAR" in pendientes["COMPRAS_PREPARAR"]


def main():
    test_planificador_flujo_completo()
    test_planificador_detecta_dependencia_faltante()
    print("TEST OK 5.3.5 Planificador Inteligente")


if __name__ == "__main__":
    main()
