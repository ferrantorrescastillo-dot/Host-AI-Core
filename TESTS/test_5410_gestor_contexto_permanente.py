from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.gestor_contexto_permanente_5410 import GestorContextoPermanente5410
from SERVICIOS.orquestador_inteligente_52 import OrquestadorInteligente52


def test_gestor_basico():
    g = GestorContextoPermanente5410()
    g.activar_flujo({"evento": {"tipo": "boda"}, "estado_conversacion": "pendiente_confirmacion"})
    assert g.esta_activo()
    g.cambiar_estado("esperando_seleccion_accion")
    assert g.estado() == "esperando_seleccion_accion"
    assert g.obtener("evento")["tipo"] == "boda"


def test_contexto_no_se_pierde_tras_si():
    o = OrquestadorInteligente52(BASE_DIR)
    # Inyectamos un flujo válido para aislar la prueba de continuidad.
    flujo = {"ok": True, "datos": {"tipo":"boda","personas":150,"fecha":"sabado","hora_servicio":"15:00","menu":"paella","lugar":"restaurante","restricciones":"sin restricciones","objetivo":"flujo completo"}, "pasos": []}
    o.gestor_contexto_5410.activar_flujo({"flujo_pendiente_confirmacion": True, "datos_flujo": flujo["datos"], "flujo": flujo, "confirmaciones": {"acciones_con_confirmacion": []}})
    o.contexto_activo_549 = o.gestor_contexto_5410.contexto
    r = o.procesar("sí")
    assert r["intencion"] == "confirmacion_flujo"
    assert o.gestor_contexto_5410.esta_activo()
    assert o.gestor_contexto_5410.estado() == "flujo_revisado_esperando_siguiente_accion"


if __name__ == "__main__":
    test_gestor_basico(); test_contexto_no_se_pierde_tras_si()
    print("TEST OK 5.4.10 Gestor de Contexto Permanente")
