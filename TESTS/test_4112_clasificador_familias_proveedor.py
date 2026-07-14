import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.clasificador_familias_proveedor_4112 import ClasificadorFamiliasProveedor4112


def main():
    articulos = [
        {"codigo": "ART000001", "nombre": "Producto verde", "proveedor": "PAU GAVALDA", "familia": ""},
        {"codigo": "ART000002", "nombre": "Botella prueba", "proveedor": "Disbesa.", "familia": ""},
        {"codigo": "ART000003", "nombre": "Longaniza fresca", "proveedor": "Cualquiera", "familia": ""},
        {"codigo": "ART000004", "nombre": "Ya tiene familia", "proveedor": "PAU GAVALDA", "familia": "Manual"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_db = Path(tmpdir) / "articulos.json"
        ruta_txt = Path(tmpdir) / "informe.txt"
        ruta_db.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding="utf-8")

        clasificador = ClasificadorFamiliasProveedor4112(str(ruta_db))
        informe = clasificador.exportar_informe_txt(str(ruta_txt))

        assert informe.total_articulos == 4
        assert informe.sin_familia_antes == 3
        assert informe.familias_aplicadas == 3
        assert informe.sin_familia_despues == 0
        assert ruta_txt.exists()

        datos = json.loads(ruta_db.read_text(encoding="utf-8"))
        assert next(a for a in datos if a["codigo"] == "ART000001")["familia"] == "Verduras"
        assert next(a for a in datos if a["codigo"] == "ART000002")["familia"] == "Bebidas"
        assert next(a for a in datos if a["codigo"] == "ART000003")["familia"] == "Carnes"

    print("TEST OK - Host AI 4.1.12 Clasificador por Proveedor")
    print("Familias aplicadas:", informe.familias_aplicadas)
    print("Sin familia después:", informe.sin_familia_despues)


if __name__ == "__main__":
    main()
