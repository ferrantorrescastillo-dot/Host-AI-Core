import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from SERVICIOS.material_evento_476 import calcular_material_evento, comparar_material_disponible, resumen_material_evento


def main():
    evento = {"id_evento": "EVT1", "personas": 140, "tipo": "paella"}
    menu = {"platos": ["Aperitivo", "Paella de marisco", "Postre"]}
    plan = calcular_material_evento(evento, menu)
    assert plan["ok"] is True
    assert plan["material"]["paelleras"] >= 4
    comp = comparar_material_disponible(plan, {"paelleras": 1})
    assert comp["ok"] is False
    assert comp["faltantes"]
    assert "MATERIAL EVENTO" in resumen_material_evento(plan)
    print("TEST OK 4.7.6 Material evento")


if __name__ == "__main__":
    main()
