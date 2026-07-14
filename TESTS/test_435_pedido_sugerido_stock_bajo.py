import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.generador_pedido_stock_bajo_435 import GeneradorPedidoStockBajo435


def main():
    stock = [
        {"codigo": "ART000001", "articulo": "Aceite", "proveedor": "Makro", "familia": "Aceites", "unidad": "l", "stock_actual": 1, "stock_minimo": 3, "ubicacion": "Seco"},
        {"codigo": "ART000002", "articulo": "Arroz", "proveedor": "Makro", "familia": "Arroces", "unidad": "kg", "stock_actual": 8, "stock_minimo": 5, "ubicacion": "Seco"},
        {"codigo": "ART000003", "articulo": "Tomate", "proveedor": "Pau Gavalda", "familia": "Verduras", "unidad": "kg", "stock_actual": 0, "stock_minimo": 4, "ubicacion": "Cámara"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_stock = Path(tmpdir) / "stock.json"
        ruta_json = Path(tmpdir) / "pedido.json"
        ruta_txt = Path(tmpdir) / "pedido.txt"
        ruta_stock.write_text(json.dumps(stock, ensure_ascii=False, indent=2), encoding="utf-8")

        generador = GeneradorPedidoStockBajo435(str(ruta_stock))
        informe = generador.generar(str(ruta_json), str(ruta_txt))

        assert informe.total_lineas == 2
        assert informe.total_proveedores == 2
        assert informe.estado == "pedido_sugerido"
        assert ruta_json.exists()
        assert ruta_txt.exists()

    print("TEST OK - Host AI 4.3.5 Pedido Sugerido Stock Bajo")
    print("Líneas:", informe.total_lineas)
    print("Proveedores:", informe.total_proveedores)


if __name__ == "__main__":
    main()
