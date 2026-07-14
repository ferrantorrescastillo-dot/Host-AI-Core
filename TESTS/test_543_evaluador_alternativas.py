from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.evaluador_alternativas_543 import evaluar_alternativas_543


def _evento():
    return {"tipo":"boda","personas":180,"fecha":"sabado","hora_servicio":"15:00","menu":"paella","lugar":"Restaurante","restricciones":"sin restricciones","objetivo":"todo el flujo completo"}


def test_evalua_alternativas_stock_y_proveedor():
    contexto = {
        "stock": [{"nombre":"arroz bomba","disponible":10,"necesario":20}],
        "proveedores": [{"nombre":"Makro","disponible":False}],
        "personal": {"disponibles":2,"necesarios":3},
    }
    r = evaluar_alternativas_543(_evento(), contexto)
    assert r["ok"] is True
    assert r["version"] == "5.4.3"
    assert r["bloques"]
    assert r["recomendacion_global"] is not None
    assert r["aplicado"] is False
    codigos = {a["codigo"] for a in r["alternativas"]}
    assert "ALT_PROVEEDOR_ALTERNATIVO" in codigos or "ALT_COMPRA_HABITUAL" in codigos


def test_alternativas_tienen_puntuacion():
    r = evaluar_alternativas_543(_evento(), {})
    assert r["ok"] is True
    assert all("puntuacion" in a for a in r["alternativas"])


if __name__ == "__main__":
    test_evalua_alternativas_stock_y_proveedor()
    test_alternativas_tienen_puntuacion()
    print("TEST OK 5.4.3 Evaluador Inteligente de Alternativas")
