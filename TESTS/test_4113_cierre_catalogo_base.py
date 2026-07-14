import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.cierre_catalogo_base_4113 import CierreCatalogoBase4113


def main():
    articulos = [
        {"codigo": "ART000001", "nombre": "Aceite", "proveedor": "Makro", "familia": "Aceites", "precio": 8.5},
        {"codigo": "ART000002", "nombre": "Sin precio", "proveedor": "Makro", "familia": "Varios", "precio": None},
    ]
    proveedores = [
        {"codigo": "PROV0001", "nombre": "Makro", "variantes_detectadas": ["Makro"]},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_articulos = Path(tmpdir) / "articulos.json"
        ruta_proveedores = Path(tmpdir) / "proveedores.json"
        ruta_txt = Path(tmpdir) / "cierre.txt"

        ruta_articulos.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding="utf-8")
        ruta_proveedores.write_text(json.dumps(proveedores, ensure_ascii=False, indent=2), encoding="utf-8")

        cierre = CierreCatalogoBase4113(str(ruta_articulos), str(ruta_proveedores))
        informe = cierre.exportar_txt(str(ruta_txt))

        assert informe.total_articulos == 2
        assert informe.total_proveedores == 1
        assert informe.sin_precio == 1
        assert informe.estado == "apto_con_observaciones"
        assert "Host AI 4.3" in informe.bloque_siguiente
        assert ruta_txt.exists()

    print("TEST OK - Host AI 4.1.13 Cierre Catálogo Base")
    print("Estado:", informe.estado)
    print("Bloque siguiente:", informe.bloque_siguiente)


if __name__ == "__main__":
    main()
