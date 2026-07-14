import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.informe_catalogo_articulos_418 import InformeCatalogoArticulos418


def main():
    articulos = [
        {"codigo": "ART000001", "nombre": "Aceite", "proveedor": "Makro", "familia": "Aceites", "precio": 8.5, "activo": True, "origen": "excel"},
        {"codigo": "ART000002", "nombre": "Arroz bomba", "proveedor": "Makro", "familia": "Arroces", "precio": 3.2, "activo": True, "origen": "alta_manual_416"},
        {"codigo": "ART000003", "nombre": "Sin proveedor", "proveedor": None, "familia": "", "precio": 0, "activo": True, "origen": "excel"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_db = Path(tmpdir) / "articulos.json"
        ruta_txt = Path(tmpdir) / "informe.txt"
        ruta_db.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding="utf-8")

        generador = InformeCatalogoArticulos418(str(ruta_db))
        informe = generador.exportar_txt(str(ruta_txt))

        assert informe.total_articulos == 3
        assert informe.sin_proveedor == 1
        assert informe.sin_familia == 1
        assert informe.precio_cero == 1
        assert informe.estado == "apto_con_observaciones"
        assert ruta_txt.exists()

    print("TEST OK - Host AI 4.1.8 Informe Catálogo de Artículos")
    print("Estado:", informe.estado)
    print("Artículos:", informe.total_articulos)


if __name__ == "__main__":
    main()
