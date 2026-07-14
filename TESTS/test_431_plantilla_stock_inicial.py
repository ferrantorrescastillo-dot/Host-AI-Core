import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.generador_plantilla_stock_inicial_431 import GeneradorPlantillaStockInicial431


def main():
    articulos = [
        {"codigo": "ART000001", "nombre": "Aceite", "proveedor": "Makro", "familia": "Aceites"},
        {"codigo": "ART000002", "nombre": "Arroz bomba", "proveedor": "Makro", "familia": "Arroces"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_articulos = Path(tmpdir) / "articulos.json"
        ruta_excel = Path(tmpdir) / "stock.xlsx"
        ruta_articulos.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding="utf-8")

        generador = GeneradorPlantillaStockInicial431(str(ruta_articulos))
        resultado = generador.generar_excel(str(ruta_excel))

        assert resultado.total_articulos == 2
        assert resultado.estado == "ok"
        assert ruta_excel.exists()

    print("TEST OK - Host AI 4.3.1 Plantilla Stock Inicial")
    print("Artículos plantilla:", resultado.total_articulos)


if __name__ == "__main__":
    main()
