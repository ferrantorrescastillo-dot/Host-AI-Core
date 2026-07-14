import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.informe_proveedores_423 import InformeProveedores423


def main():
    proveedores = [
        {"codigo": "PROV0001", "nombre": "Makro", "estado": "activo", "articulos_asociados": 5, "variantes_detectadas": ["Makro", "MAKRO."]},
        {"codigo": "PROV0002", "nombre": "Pau Gavalda", "estado": "activo", "articulos_asociados": 3, "variantes_detectadas": ["Pau Gavalda"]},
    ]
    articulos = [
        {"codigo": "ART000001", "nombre": "Aceite", "proveedor": "Makro"},
        {"codigo": "ART000002", "nombre": "Sin proveedor", "proveedor": ""},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_prov = Path(tmpdir) / "proveedores.json"
        ruta_art = Path(tmpdir) / "articulos.json"
        ruta_txt = Path(tmpdir) / "informe.txt"
        ruta_prov.write_text(json.dumps(proveedores, ensure_ascii=False, indent=2), encoding="utf-8")
        ruta_art.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding="utf-8")

        generador = InformeProveedores423(str(ruta_prov), str(ruta_art))
        informe = generador.exportar_txt(str(ruta_txt))

        assert informe.total_proveedores == 2
        assert informe.proveedores_con_variantes == 1
        assert informe.articulos_sin_proveedor == 1
        assert informe.estado == "apto_con_observaciones"
        assert ruta_txt.exists()

    print("TEST OK - Host AI 4.2.3 Informe de Proveedores")
    print("Proveedores:", informe.total_proveedores)
    print("Estado:", informe.estado)


if __name__ == "__main__":
    main()
