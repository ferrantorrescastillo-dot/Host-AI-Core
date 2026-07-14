import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.clasificador_familias_articulos_419 import ClasificadorFamiliasArticulos419


def main():
    articulos = [
        {"codigo": "ART000001", "nombre": "Arroz bomba", "familia": ""},
        {"codigo": "ART000002", "nombre": "Aceite oliva", "familia": None},
        {"codigo": "ART000003", "nombre": "Coca Cola 33cl", "familia": ""},
        {"codigo": "ART000004", "nombre": "Coca de recapte", "familia": ""},
        {"codigo": "ART000005", "nombre": "Producto raro", "familia": ""},
        {"codigo": "ART000006", "nombre": "Ya clasificado", "familia": "Manual"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_db = Path(tmpdir) / "articulos.json"
        ruta_txt = Path(tmpdir) / "informe.txt"
        ruta_db.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding="utf-8")

        clasificador = ClasificadorFamiliasArticulos419(str(ruta_db))
        informe = clasificador.exportar_informe_txt(str(ruta_txt))

        assert informe.total_articulos == 6
        assert informe.sin_familia_antes == 5
        assert informe.familias_aplicadas == 4
        assert informe.sin_familia_despues == 1
        assert informe.estado == "apto_con_observaciones"
        assert ruta_txt.exists()

        datos = json.loads(ruta_db.read_text(encoding="utf-8"))
        arroz = next(a for a in datos if a["codigo"] == "ART000001")
        aceite = next(a for a in datos if a["codigo"] == "ART000002")
        coca_cola = next(a for a in datos if a["codigo"] == "ART000003")
        coca_pan = next(a for a in datos if a["codigo"] == "ART000004")
        manual = next(a for a in datos if a["codigo"] == "ART000006")

        assert arroz["familia"] == "Arroces y cereales"
        assert aceite["familia"] == "Aceites"
        assert coca_cola["familia"] == "Bebidas"
        assert coca_pan["familia"] == "Panadería"
        assert manual["familia"] == "Manual"

    print("TEST OK - Host AI 4.1.9.1 Clasificador de Familias FIX")
    print("Familias aplicadas:", informe.familias_aplicadas)
    print("Sin familia después:", informe.sin_familia_despues)


if __name__ == "__main__":
    main()
