from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.optimizador_global_545 import optimizar_operacion_545, formatear_optimizacion_545


def test_545_basico():
    evento = {"tipo": "boda", "personas": 180, "menu": "paella"}
    contexto = {"personal": {"disponibles": 2, "necesarios": 3}}
    r = optimizar_operacion_545(evento, contexto)
    assert r["ok"] is True
    assert r["version"] == "5.4.5"
    assert r["aplicado"] is False
    assert r["requiere_confirmacion"] is True
    assert r["plan_recomendado"]
    assert len(r["planes"]) >= 3
    txt = formatear_optimizacion_545(r)
    assert "OPTIMIZADOR GLOBAL" in txt
    assert "Confirmacion necesaria" in txt


if __name__ == "__main__":
    test_545_basico()
    print("TEST OK 5.4.5 Optimizador Global")
