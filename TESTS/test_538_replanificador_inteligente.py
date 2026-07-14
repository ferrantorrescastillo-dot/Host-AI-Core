from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.detector_incidencias_537 import detectar_incidencias_operativas
from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento
from SERVICIOS.planificador_inteligente_535 import planificar_ejecucion_inteligente
from SERVICIOS.priorizador_tareas_536 import priorizar_tareas_operativas
from SERVICIOS.replanificador_inteligente_538 import replanificar_operativa_inteligente


def _preparar():
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
    contexto = {
        "stock": [{"nombre": "arroz bomba", "disponible": 8, "necesario": 18, "unidad": "kg", "imprescindible": True}],
        "proveedores": [{"nombre": "Proveedor habitual", "disponible": False}],
        "tareas": [{"nombre": "Marcar fondos", "requiere_responsable": True}],
    }
    flujo = generar_flujo_operativo_evento(datos)
    plan = planificar_ejecucion_inteligente(flujo)
    prioridades = priorizar_tareas_operativas(plan)
    incidencias = detectar_incidencias_operativas(plan, prioridades, contexto)
    return plan, incidencias, contexto


def test_replanificador_propone_sin_aplicar():
    plan, incidencias, contexto = _preparar()
    resultado = replanificar_operativa_inteligente(plan, incidencias, contexto)
    assert resultado["ok"] is True
    assert resultado["estado"] == "replanificacion_propuesta"
    assert resultado["requiere_confirmacion"] is True
    assert resultado["aplicado"] is False
    assert resultado["nuevo_planning"]
    assert resultado["nuevo_planning"][0]["origen"] == "incidencia"
    assert any(t["grupo"] == "compras_urgentes" for t in resultado["nuevo_planning"])
    assert resultado["soluciones"]


def test_replanificador_sin_incidencias_mantiene_plan():
    plan, _, _ = _preparar()
    resultado = replanificar_operativa_inteligente(plan, {"incidencias": []})
    assert resultado["ok"] is True
    assert resultado["estado"] == "sin_cambios"
    assert resultado["requiere_confirmacion"] is False
    assert resultado["nuevo_planning"]


def main():
    test_replanificador_propone_sin_aplicar()
    test_replanificador_sin_incidencias_mantiene_plan()
    print("TEST OK 5.3.8 Replanificador Inteligente")


if __name__ == "__main__":
    main()
