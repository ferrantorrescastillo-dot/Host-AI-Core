import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.gestor_pendientes_recepcion_444 import GestorPendientesRecepcion444


def main():
    recepcion = {
        "proveedor": "Makro",
        "lineas": [
            {"codigo": "ART000001", "articulo": "Arroz bomba", "cantidad": 15, "unidad": "kg"},
            {"articulo": "Harina fuerza premium", "cantidad": 5, "unidad": "kg", "precio_unitario": "1,20"},
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_rec = Path(tmpdir) / "recepcion.json"
        ruta_art = Path(tmpdir) / "articulos.json"
        ruta_json = Path(tmpdir) / "pendientes.json"
        ruta_txt = Path(tmpdir) / "pendientes.txt"

        ruta_rec.write_text(json.dumps(recepcion, ensure_ascii=False, indent=2), encoding="utf-8")
        ruta_art.write_text("[]", encoding="utf-8")

        gestor = GestorPendientesRecepcion444(str(ruta_rec), str(ruta_art))
        revision = gestor.exportar(crear=False, ruta_json=str(ruta_json), ruta_txt=str(ruta_txt))

        assert revision.total_pendientes == 1
        assert revision.creados == 0
        assert revision.no_creados == 1

        creado = gestor.exportar(crear=True, ruta_json=str(ruta_json), ruta_txt=str(ruta_txt))
        assert creado.total_pendientes == 1
        assert creado.creados == 1

        articulos = json.loads(ruta_art.read_text(encoding="utf-8"))
        assert len(articulos) == 1
        assert articulos[0]["nombre"] == "Harina fuerza premium"
        assert articulos[0]["familia"] == "Harinas"

    print("TEST OK - Host AI 4.4.4 Gestor Pendientes Recepción")
    print("Pendientes:", revision.total_pendientes)
    print("Creados:", creado.creados)


if __name__ == "__main__":
    main()
