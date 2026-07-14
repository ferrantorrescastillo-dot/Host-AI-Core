from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.explicacion_decisiones_547 import explicar_decisiones_547, formatear_explicacion_547


def test_547_basico():
    decisiones = [
        {"area": "stock", "prioridad": "alta", "accion": "Revisar arroz bomba", "razon": "Ingrediente critico", "requiere_confirmacion": False},
        {"area": "compras", "prioridad": "media", "accion": "Preparar pedido", "razon": "Falta stock", "requiere_confirmacion": True},
    ]
    r = explicar_decisiones_547({"personas": 180}, decisiones)
    assert r["ok"] is True
    assert r["version"] == "5.4.7"
    assert r["decisiones_explicadas"] == 2
    assert r["requiere_confirmacion"] is True
    assert "arroz" in r["explicaciones"][0]["accion"].lower()
    txt = formatear_explicacion_547(r)
    assert "EXPLICACION INTELIGENTE" in txt
    assert "Por que" in txt


if __name__ == "__main__":
    test_547_basico()
    print("TEST OK 5.4.7 Explicacion Inteligente de Decisiones")
