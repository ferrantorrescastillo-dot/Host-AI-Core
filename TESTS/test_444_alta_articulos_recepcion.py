import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.alta_articulos_recepcion_444 import AltaArticulosDesdeRecepcion444


def main():
    articulos = [
        {"codigo": "ART000001", "nombre": "Arroz bomba", "proveedor": "Makro", "familia": "Arroces", "precio": 3.0, "activo": True}
    ]
    borrador = {
        "lineas_validadas": [
            {
                "producto_texto": "harina fuerza",
                "cantidad": 5,
                "unidad": "kg",
                "proveedor_texto": "Makro",
                "precio_unitario": 1.2,
                "accion_sugerida": "crear_articulo_pendiente",
            },
            {
                "producto_texto": "arroz bomba",
                "cantidad": 15,
                "unidad": "kg",
                "proveedor_texto": "Makro",
                "precio_unitario": 3.2,
                "accion_sugerida": "entrada_stock",
            },
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        db = Path(tmpdir)
        ruta_art = db / "articulos.json"
        ruta_borrador = db / "recepcion_borrador.json"
        ruta_json = db / "nuevos.json"
        ruta_txt = db / "nuevos.txt"

        ruta_art.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding="utf-8")
        ruta_borrador.write_text(json.dumps(borrador, ensure_ascii=False, indent=2), encoding="utf-8")

        alta = AltaArticulosDesdeRecepcion444(str(ruta_borrador), str(ruta_art))
        resultado = alta.crear_y_exportar(str(ruta_json), str(ruta_txt))

        assert resultado.total_pendientes == 1
        assert resultado.creados == 1
        assert resultado.no_creados == 0
        assert resultado.estado == "creados"

        articulos_final = json.loads(ruta_art.read_text(encoding="utf-8"))
        assert len(articulos_final) == 2
        nuevo = next(a for a in articulos_final if a["nombre"] == "harina fuerza")
        assert nuevo["codigo"] == "ART000002"
        assert nuevo["proveedor"] == "Makro"
        assert nuevo["precio"] == 1.2
        assert ruta_json.exists()
        assert ruta_txt.exists()

    print("TEST OK - Host AI 4.4.4 Alta Artículos desde Recepción")
    print("Creados:", resultado.creados)


if __name__ == "__main__":
    main()
