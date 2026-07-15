from pathlib import Path
import json
import sys
import tempfile

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.conector_produccion_real_556 import procesar_consulta_produccion_real_556
from SERVICIOS.orquestador_inteligente_52 import OrquestadorInteligente52


def _snapshot_db(db: Path) -> dict[str, str]:
    salida = {}
    for p in sorted(db.rglob("*")):
        if p.is_file():
            salida[str(p.relative_to(db)).replace("\\", "/")] = p.read_text(encoding="utf-8")
    return salida


def preparar_base() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="hostai556_"))
    db = tmp / "DATOS" / "db"
    db.mkdir(parents=True)
    (db / "escandallos_canonicos.json").write_text(json.dumps({
        "escandallos": [{
            "receta": {
                "codigo": "REC-PAELLA-MARISCO",
                "nombre": "Paella de marisco",
                "rendimiento": 10,
                "unidad_rendimiento": "personas",
                "ingredientes": [
                    {"nombre": "Arroz bomba", "articulo_id": "ART-ARROZ", "cantidad": 1.0, "unidad": "kg"},
                    {"nombre": "Caldo de pescado", "articulo_id": "ART-CALDO", "cantidad": 5.0, "unidad": "L"},
                ],
            }
        }]
    }, ensure_ascii=False), encoding="utf-8")
    (db / "articulos.json").write_text(json.dumps([
        {"codigo": "ART-ARROZ", "nombre": "Arroz bomba", "unidad": "kg", "proveedor": "Makro"},
        {"codigo": "ART-CALDO", "nombre": "Caldo de pescado", "unidad": "L", "proveedor": "Makro"},
    ], ensure_ascii=False), encoding="utf-8")
    (db / "stock_inicial.json").write_text(json.dumps([
        {"codigo": "ART-ARROZ", "articulo": "Arroz bomba", "unidad": "kg", "stock_actual": 200.0, "stock_minimo": 5.0},
        {"codigo": "ART-CALDO", "articulo": "Caldo de pescado", "unidad": "L", "stock_actual": 1000.0, "stock_minimo": 5.0},
    ], ensure_ascii=False), encoding="utf-8")
    (db / "stock_movimientos.json").write_text("[]", encoding="utf-8")
    for fn in ("proveedores.json", "precios_proveedor.json"):
        (db / fn).write_text("[]", encoding="utf-8")
    return tmp


def main():
    base = preparar_base()
    db = base / "DATOS" / "db"
    snapshot_antes = _snapshot_db(db)

    r = procesar_consulta_produccion_real_556("Prepara la producción de paella de marisco para 150 personas", base)
    assert r["gestionado"] is True
    assert r["intencion"] == "planificar_produccion_real", r
    plan = r["datos"]
    assert plan["receta"] == "Paella de marisco", plan
    assert plan["objetivo"] == 150.0, plan
    assert plan["unidad_objetivo"] == "personas", plan
    assert len(plan["tareas"]) >= 1, plan
    assert plan["datos_reales_modificados"] is False, plan
    assert _snapshot_db(db) == snapshot_antes

    orq = OrquestadorInteligente52(base)
    rr = orq.procesar("Prepara la producción de paella de marisco para 150 personas")
    assert rr.get("gestionado") is True, rr
    assert rr.get("estado") in ("PLAN_PRELIMINAR_PREPARADO", "BLOQUEADO_POR_FALTANTES"), rr
    assert isinstance((rr.get("datos") or {}).get("tareas"), list), rr
    assert "PLAN PRELIMINAR DE PRODUCCIÓN" in rr["mensaje"]
    assert _snapshot_db(db) == snapshot_antes
    print("TEST OK 5.5.6 Conector Real de Producción")


if __name__ == "__main__":
    main()
