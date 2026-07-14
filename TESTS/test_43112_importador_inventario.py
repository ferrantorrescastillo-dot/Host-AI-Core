import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.importador_inventario_43112 import ImportadorInventario43112


def main():
    filas = [
        {
            "Codigo": "ART000001",
            "Articulo": "Arroz bomba",
            "Unidad": "kg",
            "Stock sistema": 10,
            "Stock contado": "8,5",
            "Ubicación": "Seco",
            "Proveedor": "Makro",
            "Familia": "Arroces",
            "Observaciones inventario": "Falta por producción",
        },
        {
            "Codigo": "ART000002",
            "Articulo": "Aceite",
            "Unidad": "l",
            "Stock sistema": 5,
            "Stock contado": "",
            "Ubicación": "Seco",
            "Proveedor": "Makro",
            "Familia": "Aceites",
            "Observaciones inventario": "",
        },
        {
            "Codigo": "ART000003",
            "Articulo": "Tomate",
            "Unidad": "kg",
            "Stock sistema": 4,
            "Stock contado": "-1",
            "Ubicación": "Cámara",
            "Proveedor": "Pau",
            "Familia": "Verduras",
            "Observaciones inventario": "",
        },
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_json = Path(tmpdir) / "inventario.json"

        importador = ImportadorInventario43112()
        resultado = importador.importar_filas(filas, str(ruta_json))

        assert resultado.total_filas == 3
        assert resultado.importados == 1
        assert resultado.ignorados == 1
        assert resultado.errores == 1
        assert ruta_json.exists()

        datos = json.loads(ruta_json.read_text(encoding="utf-8"))
        assert len(datos) == 1
        assert datos[0]["codigo"] == "ART000001"
        assert datos[0]["stock_sistema"] == 10
        assert datos[0]["stock_contado"] == 8.5
        assert datos[0]["diferencia"] == -1.5

    print("TEST OK - Host AI 4.3.11.2 Importador Inventario")
    print("Importados:", resultado.importados)
    print("Ignorados:", resultado.ignorados)
    print("Errores:", resultado.errores)


if __name__ == "__main__":
    main()
