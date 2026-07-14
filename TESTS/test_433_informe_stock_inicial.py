import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.informe_stock_inicial_433 import InformeStockInicial433


def main():
    articulos = [
        {"codigo": "ART000001", "nombre": "Aceite"},
        {"codigo": "ART000002", "nombre": "Arroz"},
        {"codigo": "ART000003", "nombre": "Tomate"},
    ]
    stock = [
        {"codigo": "ART000001", "articulo": "Aceite", "unidad": "l", "stock_actual": 2, "stock_minimo": 3, "ubicacion": "Almacén seco"},
        {"codigo": "ART000002", "articulo": "Arroz", "unidad": "kg", "stock_actual": 10, "stock_minimo": 2, "ubicacion": ""},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_art = Path(tmpdir) / "articulos.json"
        ruta_stock = Path(tmpdir) / "stock_inicial.json"
        ruta_txt = Path(tmpdir) / "informe.txt"

        ruta_art.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding="utf-8")
        ruta_stock.write_text(json.dumps(stock, ensure_ascii=False, indent=2), encoding="utf-8")

        generador = InformeStockInicial433(str(ruta_stock), str(ruta_art))
        informe = generador.exportar_txt(str(ruta_txt))

        assert informe.total_registros_stock == 2
        assert informe.articulos_totales_catalogo == 3
        assert informe.articulos_sin_stock_cargado == 1
        assert informe.bajo_minimo == 1
        assert informe.sin_ubicacion == 1
        assert informe.estado == "apto_con_observaciones"
        assert ruta_txt.exists()

    print("TEST OK - Host AI 4.3.3 Informe Stock Inicial")
    print("Estado:", informe.estado)
    print("Alertas:", len(informe.alertas))


if __name__ == "__main__":
    main()
