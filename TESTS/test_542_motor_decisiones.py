from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.analizador_situacion_541 import analizar_situacion_operativa_541
from SERVICIOS.motor_decisiones_542 import tomar_decisiones_operativas_542


def _evento():
    return {"tipo":"boda","personas":180,"fecha":"sabado","hora_servicio":"15:00","menu":"paella","lugar":"Restaurante","restricciones":"sin restricciones","objetivo":"todo el flujo completo"}


def test_decide_sobre_faltantes_y_proveedor():
    contexto = {
        "stock": [{"nombre":"arroz bomba","disponible":10,"necesario":20}],
        "proveedores": [{"nombre":"Makro","disponible":False}],
        "personal": {"disponibles":2,"necesarios":3},
    }
    r = tomar_decisiones_operativas_542(_evento(), contexto)
    codigos = {d["codigo"] for d in r["decisiones"]}
    assert r["ok"] is True
    assert r["version"] == "5.4.2"
    assert "DEC_COMPRAS_URGENTES" in codigos
    assert "DEC_PROVEEDOR_ALTERNATIVO" in codigos
    assert r["requiere_confirmacion"] is True
    assert r["aplicado"] is False


def test_acepta_analisis_precalculado():
    analisis = analizar_situacion_operativa_541(_evento(), {})
    r = tomar_decisiones_operativas_542(analisis=analisis)
    assert r["ok"] is True
    assert r["decisiones"]
    assert r["analisis"]["version"] == "5.4.1"


if __name__ == "__main__":
    test_decide_sobre_faltantes_y_proveedor()
    test_acepta_analisis_precalculado()
    print("TEST OK 5.4.2 Motor de Toma de Decisiones")
