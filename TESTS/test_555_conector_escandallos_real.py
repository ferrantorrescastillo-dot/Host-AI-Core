from pathlib import Path
import json
import sys
import tempfile

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.conector_escandallos_real_555 import procesar_consulta_escandallos_real_555
from SERVICIOS.orquestador_inteligente_52 import OrquestadorInteligente52


def preparar_base() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="hostai555_"))
    db = tmp / "DATOS" / "db"
    db.mkdir(parents=True)
    (db / "escandallos.json").write_text(json.dumps([{
        "receta_id": "REC-PAELLA-MARISCO", "nombre": "Paella de marisco", "raciones_base": 10,
        "lineas": [
            {"nombre": "Arroz bomba", "cantidad": 1.0, "unidad": "kg", "coste_unitario": 2.15},
            {"nombre": "Caldo de pescado", "cantidad": 5.0, "unidad": "L", "coste_unitario": 1.2},
        ]
    }], ensure_ascii=False), encoding="utf-8")
    (db / "articulos.json").write_text("[]", encoding="utf-8")
    for fn in ("stock_inicial.json", "stock_movimientos.json", "proveedores.json", "precios_proveedor.json"):
        (db / fn).write_text("[]", encoding="utf-8")
    return tmp


def main():
    base = preparar_base()
    r = procesar_consulta_escandallos_real_555("Receta de paella de marisco para 150 personas", base)
    assert r["gestionado"] is True
    assert r["datos"]["encontrado"] is True, r
    esc = r["datos"]["coincidencias"][0]
    assert esc["ingredientes"][0]["cantidad"] == 15.0, esc
    assert esc["ingredientes"][1]["cantidad"] == 75.0, esc

    orq = OrquestadorInteligente52(base)
    rr = orq.procesar("¿En qué recetas uso arroz bomba?")
    assert rr["intencion"] == "consultar_escandallos_reales", rr
    assert "Paella de marisco" in rr["mensaje"]
    print("TEST OK 5.5.5 Conector Real de Escandallos y Recetas")


if __name__ == "__main__":
    main()
