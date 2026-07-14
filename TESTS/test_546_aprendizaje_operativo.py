from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.aprendizaje_operativo_546 import aprender_operativa_546, formatear_aprendizaje_546


def test_546_basico():
    historico = [
        {"dia": "sabado", "personas": 180, "compras": [{"articulo": "arroz bomba", "proveedor": "Makro"}], "tareas": [{"nombre": "paella", "tiempo_real_h": 3.5, "responsable": "Juan"}], "incidencias": [{"tipo": "falta_stock"}]},
        {"dia": "sabado", "personas": 120, "compras": [{"articulo": "arroz bomba", "proveedor": "Makro"}], "tareas": [{"nombre": "paella", "tiempo_real_h": 3.0, "responsable": "Juan"}], "incidencias": []},
    ]
    r = aprender_operativa_546(historico)
    assert r["ok"] is True
    assert r["version"] == "5.4.6"
    assert r["aplicado"] is False
    assert r["aprendizajes"]["proveedores_preferidos"]["arroz bomba"] == "Makro"
    assert r["aprendizajes"]["responsables_recomendados"]["paella"] == "Juan"
    txt = formatear_aprendizaje_546(r)
    assert "APRENDIZAJE OPERATIVO" in txt
    assert "Makro" in txt


if __name__ == "__main__":
    test_546_basico()
    print("TEST OK 5.4.6 Aprendizaje Operativo")
