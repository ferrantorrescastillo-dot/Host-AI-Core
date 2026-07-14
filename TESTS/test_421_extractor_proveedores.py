import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.extractor_proveedores_421 import ExtractorProveedores421


def main():
    articulos = [
        {"codigo": "ART000001", "nombre": "Aceite", "proveedor": "Makro"},
        {"codigo": "ART000002", "nombre": "Arroz bomba", "proveedor": "MAKRO."},
        {"codigo": "ART000003", "nombre": "Tomate", "proveedor": "Pau Gavalda"},
        {"codigo": "ART000004", "nombre": "Sin proveedor", "proveedor": ""},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_articulos = Path(tmpdir) / "articulos.json"
        ruta_proveedores = Path(tmpdir) / "proveedores.json"

        ruta_articulos.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding="utf-8")

        extractor = ExtractorProveedores421(str(ruta_articulos), str(ruta_proveedores))
        informe = extractor.extraer()

        assert informe.total_articulos == 4
        assert informe.articulos_sin_proveedor == 1
        assert informe.proveedores_detectados == 2
        assert informe.duplicados_sospechosos == 1
        assert informe.estado == "apto_con_observaciones"
        assert ruta_proveedores.exists()

        proveedores = json.loads(ruta_proveedores.read_text(encoding="utf-8"))
        assert len(proveedores) == 2
        makro = next(p for p in proveedores if p["nombre_normalizado"] == "makro")
        assert makro["articulos_asociados"] == 2
        assert len(makro["variantes_detectadas"]) == 2

    print("TEST OK - Host AI 4.2.1 Extractor de Proveedores")
    print("Proveedores detectados:", informe.proveedores_detectados)
    print("Sin proveedor:", informe.articulos_sin_proveedor)
    print("Duplicados sospechosos:", informe.duplicados_sospechosos)


if __name__ == "__main__":
    main()
