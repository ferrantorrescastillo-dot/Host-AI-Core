from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento
from SERVICIOS.planificador_inteligente_535 import planificar_ejecucion_inteligente
from SERVICIOS.priorizador_tareas_536 import priorizar_tareas_operativas


def test_priorizador_clasifica_tareas():
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
    resultado = priorizar_tareas_operativas(plan)
    assert resultado["ok"] is True
    assert resultado["estado"] == "priorizado"
    assert resultado["total_tareas"] == plan["total_pasos"]
    alta = [t["codigo"] for t in resultado["prioridades"]["alta"]]
    media = [t["codigo"] for t in resultado["prioridades"]["media"]]
    baja = [t["codigo"] for t in resultado["prioridades"]["baja"]]
    assert "EVENTO_CREAR" in alta
    assert "COMPRAS_PREPARAR" in alta
    assert "PRODUCCION_PLAN" in media
    assert "COSTES_CALCULAR" in baja


def test_priorizador_rechaza_plan_invalido():
    resultado = priorizar_tareas_operativas({"ok": False})
    assert resultado["ok"] is False
    assert resultado["estado"] == "no_priorizable"


def main():
    test_priorizador_clasifica_tareas()
    test_priorizador_rechaza_plan_invalido()
    print("TEST OK 5.3.6 Priorizador Inteligente")


if __name__ == "__main__":
    main()
