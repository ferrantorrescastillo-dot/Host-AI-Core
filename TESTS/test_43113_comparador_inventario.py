import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.comparador_inventario_43113 import ComparadorInventario43113


def main():
    inventario = [
        {
            "codigo": "ART000001",
            "articulo": "Arroz bomba",
            "unidad": "kg",
            "stock_sistema": 10,
            "stock_contado": 10,
            "ubicacion": "Seco",
            "proveedor": "Makro",
            "familia": "Arroces",
        },
        {
            "codigo": "ART000002",
            "articulo": "Aceite",
            "unidad": "l",
            "stock_sistema": 8,
            "stock_contado": 6,
            "ubicacion": "Seco",
            "proveedor": "Makro",
            "familia": "Aceites",
        },
        {
            "codigo": "ART000003",
            "articulo": "Tomate",
            "unidad": "kg",
            "stock_sistema": 4,
            "stock_contado": 5,
            "ubicacion": "Cámara",
            "proveedor": "Pau",
            "familia": "Verduras",
        },
        {
            "codigo": "ART000004",
            "articulo": "Gamba",
            "unidad": "kg",
            "stock_sistema": 10,
            "stock_contado": 3,
            "ubicacion": "Congelador",
            "proveedor": "Proveedor",
            "familia": "Mariscos",
        },
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_inv = Path(tmpdir) / "inventario.json"
        ruta_json = Path(tmpdir) / "comparacion.json"
        ruta_txt = Path(tmpdir) / "comparacion.txt"
        ruta_inv.write_text(json.dumps(inventario, ensure_ascii=False, indent=2), encoding="utf-8")

        comparador = ComparadorInventario43113(str(ruta_inv))
        informe = comparador.exportar(str(ruta_json), str(ruta_txt))

        assert informe.total_contados == 4
        assert informe.ok == 1
        assert informe.faltantes == 1
        assert informe.sobrantes == 1
        assert informe.revisar == 1
        assert informe.estado_general == "revisar_antes_de_aplicar"
        assert ruta_json.exists()
        assert ruta_txt.exists()

    print("TEST OK - Host AI 4.3.11.3 Comparador Inventario")
    print("OK:", informe.ok)
    print("Faltantes:", informe.faltantes)
    print("Sobrantes:", informe.sobrantes)
    print("Revisar:", informe.revisar)


if __name__ == "__main__":
    main()
