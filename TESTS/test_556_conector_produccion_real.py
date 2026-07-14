from pathlib import Path
import json
import sys
import tempfile

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.conector_produccion_real_556 import procesar_consulta_produccion_real_556
from SERVICIOS.orquestador_inteligente_52 import OrquestadorInteligente52


def preparar_base() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="hostai556_"))
    db = tmp / "DATOS" / "db"
    db.mkdir(parents=True)
    (db / "escandallos.json").write_text(json.dumps([{
        "receta_id": "REC-PAELLA-MARISCO", "nombre": "Paella de marisco", "raciones_base": 10,
        "lineas": [
            {"nombre": "Arroz bomba", "cantidad": 1.0, "unidad": "kg", "coste_unitario": 2.15},
            {"nombre": "Caldo de pescado", "cantidad": 5.0, "unidad": "L", "coste_unitario": 1.2},
        ]
    }], ensure_ascii=False), encoding="utf-8")
    for fn in ("articulos.json", "stock_inicial.json", "stock_movimientos.json", "proveedores.json", "precios_proveedor.json"):
        (db / fn).write_text("[]", encoding="utf-8")
    return tmp


def main():
    base = preparar_base()
    r = procesar_consulta_produccion_real_556("Prepara la producción de paella de marisco para 150 personas", base)
    assert r["gestionado"] is True
    assert r["datos"]["encontrado"] is True, r
    plan = r["datos"]["planes"][0]
    assert plan["ingredientes"][0]["cantidad"] == 15.0, plan
    assert plan["ingredientes"][1]["cantidad"] == 75.0, plan
    assert len(plan["tareas"]) == 4

    orq = OrquestadorInteligente52(base)
    rr = orq.procesar("Planifica la producción de paella de marisco para 150 personas")
    assert rr["intencion"] == "planificar_produccion_real", rr
    assert "PLAN DE PRODUCCIÓN REAL" in rr["mensaje"]
    print("TEST OK 5.5.6 Conector Real de Producción")


if __name__ == "__main__":
    main()
