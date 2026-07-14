from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.detector_incidencias_537 import detectar_incidencias_operativas
from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento
from SERVICIOS.planificador_inteligente_535 import planificar_ejecucion_inteligente
from SERVICIOS.priorizador_tareas_536 import priorizar_tareas_operativas


def _plan_base():
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
    prioridades = priorizar_tareas_operativas(plan)
    return plan, prioridades


def test_detector_clasifica_incidencias_operativas():
    plan, prioridades = _plan_base()
    contexto = {
        "stock": [{"nombre": "arroz bomba", "disponible": 8, "necesario": 18, "unidad": "kg", "imprescindible": True}],
        "recursos": [{"nombre": "horno 1", "estado": "ocupado", "detalle": "Está reservado por otro evento"}],
        "proveedores": [{"nombre": "Proveedor pescado", "disponible": False}],
        "tareas": [{"nombre": "Limpiar sepia", "requiere_responsable": True}],
        "personal": {"disponibles": 2, "necesarios": 3},
        "conflictos": [{"titulo": "Producción y evento pisan la cámara", "nivel": "alto"}],
    }
    resultado = detectar_incidencias_operativas(plan, prioridades, contexto)
    assert resultado["ok"] is True
    assert resultado["estado"] == "incidencias_detectadas"
    assert resultado["requiere_replanificacion"] is True
    tipos = {i["tipo"] for i in resultado["incidencias"]}
    assert "falta_stock" in tipos
    assert "recurso_ocupado" in tipos
    assert "proveedor_no_disponible" in tipos
    assert "tarea_sin_responsable" in tipos
    assert "falta_personal" in tipos
    assert resultado["resumen"]["critico"] >= 1
    assert resultado["resumen"]["alto"] >= 1


def test_detector_sin_contexto_no_inventa():
    plan, prioridades = _plan_base()
    resultado = detectar_incidencias_operativas(plan, prioridades, {})
    assert resultado["ok"] is True
    assert resultado["estado"] in {"sin_incidencias", "incidencias_detectadas"}
    assert isinstance(resultado["incidencias"], list)


def main():
    test_detector_clasifica_incidencias_operativas()
    test_detector_sin_contexto_no_inventa()
    print("TEST OK 5.3.7 Detector Inteligente de Incidencias")


if __name__ == "__main__":
    main()
