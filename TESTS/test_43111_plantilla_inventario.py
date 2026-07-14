import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.generador_plantilla_inventario_43111 import GeneradorPlantillaInventario43111


def main():
    stock = [
        {"codigo": "ART000001", "articulo": "Arroz", "unidad": "kg", "stock_actual": 10, "ubicacion": "Seco", "proveedor": "Makro", "familia": "Arroces"},
        {"codigo": "ART000002", "articulo": "Aceite", "unidad": "l", "stock_actual": 5, "ubicacion": "Seco", "proveedor": "Makro", "familia": "Aceites"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_stock = Path(tmpdir) / "stock_inicial.json"
        ruta_excel = Path(tmpdir) / "inventario.xlsx"
        ruta_stock.write_text(json.dumps(stock, ensure_ascii=False, indent=2), encoding="utf-8")

        generador = GeneradorPlantillaInventario43111(str(ruta_stock))
        resultado = generador.generar_excel(str(ruta_excel))

        assert resultado.total_registros_stock == 2
        assert resultado.estado == "ok"
        assert ruta_excel.exists()

    print("TEST OK - Host AI 4.3.11.1 Plantilla Inventario")
    print("Registros incluidos:", resultado.total_registros_stock)


if __name__ == "__main__":
    main()
