import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.cierre_modulo_stock_4312 import CierreModuloStock4312


def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Path(tmpdir) / "db"
        db.mkdir(parents=True, exist_ok=True)

        (db / "stock_inicial.json").write_text(json.dumps([
            {"codigo": "ART000001", "articulo": "Arroz", "stock_actual": 10, "unidad": "kg"}
        ], ensure_ascii=False, indent=2), encoding="utf-8")

        (db / "stock_movimientos.json").write_text(json.dumps([
            {"id_movimiento": "MOV00000001", "tipo": "entrada", "motivo": "Compra", "codigo": "ART000001"}
        ], ensure_ascii=False, indent=2), encoding="utf-8")

        (db / "pedidos_confirmados.json").write_text("[]", encoding="utf-8")
        (db / "inventario_contado_4_3_11_2.json").write_text("[]", encoding="utf-8")

        for name in [
            "informe_stock_inicial_4_3_3.txt",
            "alertas_stock_bajo_4_3_4.txt",
            "historial_movimientos_stock_4_3_10.txt",
            "informe_final_inventario_4_3_11_5.txt",
        ]:
            (db / name).write_text("ok", encoding="utf-8")

        cierre = CierreModuloStock4312(str(db))
        informe = cierre.exportar_txt(str(db / "cierre.txt"))

        assert informe.articulos_stock == 1
        assert informe.movimientos_stock == 1
        assert informe.estado_final == "cerrado"
        assert (db / "cierre.txt").exists()

    print("TEST OK - Host AI 4.3.12 Cierre Módulo Stock")
    print("Estado final:", informe.estado_final)


if __name__ == "__main__":
    main()
