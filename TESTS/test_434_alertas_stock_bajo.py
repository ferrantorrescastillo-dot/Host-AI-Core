import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.alertas_stock_bajo_434 import AlertasStockBajo434


def main():
    stock = [
        {"codigo": "ART000001", "articulo": "Aceite", "unidad": "l", "stock_actual": 0, "stock_minimo": 3, "ubicacion": "Almacén", "proveedor": "Makro", "familia": "Aceites"},
        {"codigo": "ART000002", "articulo": "Arroz", "unidad": "kg", "stock_actual": 2, "stock_minimo": 5, "ubicacion": "Seco", "proveedor": "Makro", "familia": "Arroces"},
        {"codigo": "ART000003", "articulo": "Sal", "unidad": "kg", "stock_actual": 8, "stock_minimo": 5, "ubicacion": "Seco", "proveedor": "Makro", "familia": "Condimentos"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_stock = Path(tmpdir) / "stock_inicial.json"
        ruta_txt = Path(tmpdir) / "alertas.txt"
        ruta_stock.write_text(json.dumps(stock, ensure_ascii=False, indent=2), encoding="utf-8")

        generador = AlertasStockBajo434(str(ruta_stock))
        informe = generador.exportar_txt(str(ruta_txt))

        assert informe.total_registros_stock == 3
        assert informe.total_alertas == 2
        assert informe.alertas_criticas == 1
        assert informe.alertas_altas == 1
        assert informe.estado == "revisar"
        assert ruta_txt.exists()

    print("TEST OK - Host AI 4.3.4 Alertas Stock Bajo")
    print("Alertas:", informe.total_alertas)
    print("Críticas:", informe.alertas_criticas)


if __name__ == "__main__":
    main()
