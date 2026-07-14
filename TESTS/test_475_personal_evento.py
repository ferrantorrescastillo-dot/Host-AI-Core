import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from SERVICIOS.personal_evento_475 import calcular_personal_evento, resumen_personal_evento


def main():
    evento = {"id_evento": "EVT1", "personas": 180, "tipo": "boda"}
    plan = calcular_personal_evento(evento, tipo_servicio="boda", complejidad="alta")
    assert plan["ok"] is True
    assert plan["personal"]["camarero"] >= 10
    assert plan["personal"]["cocinero"] >= 4
    assert "PERSONAL EVENTO" in resumen_personal_evento(plan)
    print("TEST OK 4.7.5 Personal evento")


if __name__ == "__main__":
    main()
