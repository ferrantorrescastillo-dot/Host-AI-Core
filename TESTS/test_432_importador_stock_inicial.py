import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.importador_stock_inicial_432 import ImportadorStockInicial432


def main():
    filas = [
        {
            "Codigo": "ART000001",
            "Articulo": "Aceite",
            "Proveedor": "Makro",
            "Familia": "Aceites",
            "Unidad": "l",
            "Stock actual": "10,5",
            "Stock mínimo": "3",
            "Ubicación": "Almacén seco",
            "Observaciones stock": "",
        },
        {
            "Codigo": "ART000002",
            "Articulo": "Arroz bomba",
            "Proveedor": "Makro",
            "Familia": "Arroces",
            "Unidad": "",
            "Stock actual": "",
            "Stock mínimo": "",
            "Ubicación": "",
            "Observaciones stock": "",
        },
        {
            "Codigo": "ART000003",
            "Articulo": "Tomate",
            "Proveedor": "Pau",
            "Familia": "Verduras",
            "Unidad": "kg",
            "Stock actual": "-1",
            "Stock mínimo": "2",
            "Ubicación": "Cámara",
            "Observaciones stock": "",
        },
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta = Path(tmpdir) / "stock_inicial.json"

        importador = ImportadorStockInicial432()
        resultado = importador.importar_filas(filas, str(ruta))

        assert resultado.total_filas == 3
        assert resultado.importados == 1
        assert resultado.ignorados == 1
        assert resultado.errores == 1
        assert ruta.exists()

        datos = json.loads(ruta.read_text(encoding="utf-8"))
        assert len(datos) == 1
        assert datos[0]["codigo"] == "ART000001"
        assert datos[0]["stock_actual"] == 10.5
        assert datos[0]["unidad"] == "l"

        resultado2 = importador.importar_filas([
            {
                "Codigo": "ART000001",
                "Articulo": "Aceite",
                "Proveedor": "Makro",
                "Familia": "Aceites",
                "Unidad": "l",
                "Stock actual": "11",
                "Stock mínimo": "4",
                "Ubicación": "Cocina",
                "Observaciones stock": "Recuento actualizado",
            }
        ], str(ruta))

        assert resultado2.actualizados == 1
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        assert len(datos) == 1
        assert datos[0]["stock_actual"] == 11.0
        assert datos[0]["ubicacion"] == "Cocina"

    print("TEST OK - Host AI 4.3.2 Importador Stock Inicial")
    print("Importados:", resultado.importados)
    print("Ignorados:", resultado.ignorados)
    print("Errores:", resultado.errores)


if __name__ == "__main__":
    main()
