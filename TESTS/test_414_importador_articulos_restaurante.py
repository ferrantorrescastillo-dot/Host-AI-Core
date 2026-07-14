import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.importador_articulos_restaurante_414 import ImportadorArticulosRestaurante414


def main():
    importador = ImportadorArticulosRestaurante414()

    filas = [
        {"Codigo": "ART000001", "Articulo": "Aceite oliva", "Observaciones": "", "Proveedor": "Makro", "Familia": "Aceites", "Precio": "8,50"},
        {"Codigo": "ART000002", "Articulo": "Arroz bomba", "Observaciones": "", "Proveedor": "Makro", "Familia": "Seco", "Precio": "3.20"},
        {"Codigo": "", "Articulo": "Sin codigo", "Observaciones": "", "Proveedor": "", "Familia": "", "Precio": "1"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_db = Path(tmpdir) / "articulos.json"

        resultado = importador.importar_filas(filas, str(ruta_db))

        assert resultado.total_procesados == 3
        assert resultado.nuevos == 2
        assert resultado.actualizados == 0
        assert resultado.errores == 1
        assert ruta_db.exists()

        articulos = json.loads(ruta_db.read_text(encoding="utf-8"))
        assert len(articulos) == 2
        assert articulos[0]["codigo"] == "ART000001"
        assert articulos[0]["nombre"] == "Aceite oliva"

        filas_actualizacion = [
            {"Codigo": "ART000001", "Articulo": "Aceite oliva virgen", "Observaciones": "", "Proveedor": "Makro", "Familia": "Aceites", "Precio": "9,10"},
        ]

        resultado2 = importador.importar_filas(filas_actualizacion, str(ruta_db))
        assert resultado2.nuevos == 0
        assert resultado2.actualizados == 1

        articulos = json.loads(ruta_db.read_text(encoding="utf-8"))
        assert len(articulos) == 2
        articulo_actualizado = next(item for item in articulos if item["codigo"] == "ART000001")
        assert articulo_actualizado["nombre"] == "Aceite oliva virgen"
        assert articulo_actualizado["precio"] == 9.10

    print("TEST OK - Host AI 4.1.4 Importador Inteligente de Artículos")
    print("Nuevos:", resultado.nuevos)
    print("Errores:", resultado.errores)


if __name__ == "__main__":
    main()
