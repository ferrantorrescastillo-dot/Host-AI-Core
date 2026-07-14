from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.release_candidate_548 import ejecutar_release_candidate_548, formatear_release_candidate_548


def test_548_basico():
    r = ejecutar_release_candidate_548({"tipo_evento": "boda", "personas": 180, "menu": "paella"})
    assert r["version"] == "5.4.8"
    assert r["etapas_total"] == 7
    assert r["aplicado"] is False
    assert r["porcentaje"] >= 85
    txt = formatear_release_candidate_548(r)
    assert "RELEASE CANDIDATE" in txt
    assert "5.4.7" in txt


if __name__ == "__main__":
    test_548_basico()
    print("TEST OK 5.4.8 Integracion Completa y Release Candidate 5.4")
