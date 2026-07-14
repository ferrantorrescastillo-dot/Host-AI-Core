from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.analizador_situacion_541 import analizar_situacion_operativa_541


def test_analiza_estado_con_riesgos():
    evento = {"tipo":"boda","personas":180,"fecha":"sabado","hora_servicio":"15:00","menu":"paella","lugar":"Restaurante","restricciones":"sin restricciones","objetivo":"todo el flujo completo"}
    contexto = {
        "stock": [{"nombre":"arroz bomba","disponible":10,"necesario":20,"unidad":"kg"}],
        "personal": {"disponibles":2,"necesarios":3},
        "recursos": [{"nombre":"horno 1","estado":"ocupado"}],
        "proveedores": [{"nombre":"Makro","disponible":False}],
    }
    r = analizar_situacion_operativa_541(evento, contexto)
    assert r["ok"] is True
    assert r["version"] == "5.4.1"
    assert r["riesgo_general"] in {"critico", "alto"}
    assert r["componentes"]["stock"]["estado"] == "faltante"
    assert r["componentes"]["personal"]["estado"] == "insuficiente"
    assert r["requiere_confirmacion"] is True


def test_analiza_estado_sin_datos_reales():
    evento = {"tipo":"evento","personas":50,"fecha":"mañana","hora_servicio":"14:00","menu":"menu diario","lugar":"Restaurante","restricciones":"sin restricciones","objetivo":"todo el flujo completo"}
    r = analizar_situacion_operativa_541(evento, {})
    assert r["ok"] is True
    assert r["componentes"]["stock"]["estado"] == "pendiente_consulta"
    assert r["componentes"]["proveedores"]["estado"] == "pendiente"


if __name__ == "__main__":
    test_analiza_estado_con_riesgos()
    test_analiza_estado_sin_datos_reales()
    print("TEST OK 5.4.1 Analizador Inteligente de Situacion")
