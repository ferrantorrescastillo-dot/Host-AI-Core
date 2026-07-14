import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.aplicador_ajustes_inventario_43114 import AplicadorAjustesInventario43114


def main():
    stock = [
        {"codigo": "ART000001", "articulo": "Arroz", "unidad": "kg", "stock_actual": 10, "stock_minimo": 5},
        {"codigo": "ART000002", "articulo": "Aceite", "unidad": "l", "stock_actual": 8, "stock_minimo": 3},
        {"codigo": "ART000003", "articulo": "Gamba", "unidad": "kg", "stock_actual": 10, "stock_minimo": 2},
    ]

    comparacion = {
        "lineas": [
            {"codigo": "ART000001", "articulo": "Arroz", "unidad": "kg", "stock_sistema": 10, "stock_contado": 8, "diferencia": -2, "estado": "faltante"},
            {"codigo": "ART000002", "articulo": "Aceite", "unidad": "l", "stock_sistema": 8, "stock_contado": 9, "diferencia": 1, "estado": "sobrante"},
            {"codigo": "ART000003", "articulo": "Gamba", "unidad": "kg", "stock_sistema": 10, "stock_contado": 3, "diferencia": -7, "estado": "revisar"},
            {"codigo": "ART000004", "articulo": "Sal", "unidad": "kg", "stock_sistema": 5, "stock_contado": 5, "diferencia": 0, "estado": "ok"},
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_stock = Path(tmpdir) / "stock_inicial.json"
        ruta_mov = Path(tmpdir) / "stock_movimientos.json"
        ruta_comp = Path(tmpdir) / "comparacion.json"
        ruta_txt = Path(tmpdir) / "ajustes.txt"

        ruta_stock.write_text(json.dumps(stock, ensure_ascii=False, indent=2), encoding="utf-8")
        ruta_comp.write_text(json.dumps(comparacion, ensure_ascii=False, indent=2), encoding="utf-8")

        aplicador = AplicadorAjustesInventario43114(str(ruta_comp), str(ruta_stock), str(ruta_mov))
        resultado = aplicador.exportar_txt(str(ruta_txt))

        assert resultado.total_lineas == 4
        assert resultado.ajustes_aplicados == 2
        assert resultado.ajustes_omitidos == 2
        assert resultado.errores == 0
        assert ruta_txt.exists()

        stock_final = json.loads(ruta_stock.read_text(encoding="utf-8"))
        assert next(a for a in stock_final if a["codigo"] == "ART000001")["stock_actual"] == 8
        assert next(a for a in stock_final if a["codigo"] == "ART000002")["stock_actual"] == 9
        assert next(a for a in stock_final if a["codigo"] == "ART000003")["stock_actual"] == 10

        movimientos = json.loads(ruta_mov.read_text(encoding="utf-8"))
        assert len(movimientos) == 2
        assert movimientos[0]["tipo"] == "ajuste"

    print("TEST OK - Host AI 4.3.11.4 Aplicador Ajustes Inventario")
    print("Aplicados:", resultado.ajustes_aplicados)
    print("Omitidos:", resultado.ajustes_omitidos)


if __name__ == "__main__":
    main()
