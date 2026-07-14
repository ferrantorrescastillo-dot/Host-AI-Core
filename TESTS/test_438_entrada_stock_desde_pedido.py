import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.entrada_stock_desde_pedido_438 import EntradaStockDesdePedido438


def main():
    stock = [
        {"codigo": "ART000001", "articulo": "Aceite", "unidad": "l", "stock_actual": 1, "stock_minimo": 3},
        {"codigo": "ART000002", "articulo": "Arroz", "unidad": "kg", "stock_actual": 2, "stock_minimo": 5},
    ]

    pedidos = [
        {
            "id_pedido": "PED000001",
            "proveedor": "Makro",
            "estado": "confirmado",
            "lineas": [
                {"codigo": "ART000001", "articulo": "Aceite", "unidad": "l", "cantidad": 2, "prioridad": "alta"},
                {"codigo": "ART000002", "articulo": "Arroz", "unidad": "kg", "cantidad": 3, "prioridad": "alta"},
            ],
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_stock = Path(tmpdir) / "stock_inicial.json"
        ruta_mov = Path(tmpdir) / "stock_movimientos.json"
        ruta_ped = Path(tmpdir) / "pedidos_confirmados.json"
        ruta_txt = Path(tmpdir) / "entradas.txt"

        ruta_stock.write_text(json.dumps(stock, ensure_ascii=False, indent=2), encoding="utf-8")
        ruta_ped.write_text(json.dumps(pedidos, ensure_ascii=False, indent=2), encoding="utf-8")

        procesador = EntradaStockDesdePedido438(str(ruta_ped), str(ruta_stock), str(ruta_mov))
        resultado = procesador.exportar_txt(str(ruta_txt))

        assert resultado.pedidos_procesados == 1
        assert resultado.lineas_procesadas == 2
        assert resultado.entradas_ok == 2
        assert resultado.entradas_error == 0

        stock_final = json.loads(ruta_stock.read_text(encoding="utf-8"))
        assert next(a for a in stock_final if a["codigo"] == "ART000001")["stock_actual"] == 3
        assert next(a for a in stock_final if a["codigo"] == "ART000002")["stock_actual"] == 5

        movimientos = json.loads(ruta_mov.read_text(encoding="utf-8"))
        assert len(movimientos) == 2

        pedidos_final = json.loads(ruta_ped.read_text(encoding="utf-8"))
        assert pedidos_final[0]["estado"] == "recibido_stock"
        assert ruta_txt.exists()

    print("TEST OK - Host AI 4.3.8 Entrada Stock desde Pedido")
    print("Entradas OK:", resultado.entradas_ok)


if __name__ == "__main__":
    main()
