from __future__ import annotations

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.orquestador_inteligente_52 import OrquestadorInteligente52
from SERVICIOS.gestor_datos_minimos_52 import GestorDatosMinimos52


def test_extrae_hora_en_frase_con_pax():
    gestor = GestorDatosMinimos52()
    r = gestor.procesar("Tengo una boda para 150 personas el sábado a las 15:00 en el restaurante")
    evento = r["evento"]
    assert evento["pax"] == 150
    assert evento["hora_servicio"] == "15:00"


def test_continua_confirmacion_sin_reclasificar():
    o = OrquestadorInteligente52(BASE_DIR)
    r1 = o.procesar("Tengo una boda para 150 personas el sábado a las 15:00 en el restaurante")
    assert r1["estado"] == "faltan_datos"
    r2 = o.procesar("paella")
    assert r2["estado"] == "faltan_datos"
    r3 = o.procesar("sin restricciones")
    assert r3["estado"] == "faltan_datos"
    r4_pre = o.procesar("todo el flujo completo")
    assert r4_pre["estado"] == "flujo_evento_preparado_pendiente_confirmacion"
    r4 = o.procesar("sí")
    assert r4["estado"] == "flujo_confirmado_continuado"
    assert r4["intencion"] == "confirmacion_flujo"
    assert "Mantengo el contexto" in r4["mensaje"]


def run_all():
    test_extrae_hora_en_frase_con_pax()
    test_continua_confirmacion_sin_reclasificar()
    print("TEST OK 5.4.9 Continuidad Conversacional")


if __name__ == "__main__":
    run_all()
