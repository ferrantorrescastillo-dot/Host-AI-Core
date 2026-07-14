import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.gestor_articulos_416 import GestorArticulos416


def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_db = Path(tmpdir) / "articulos.json"
        ruta_db.write_text(json.dumps([
            {"codigo": "ART000001", "nombre": "Aceite oliva", "proveedor": "Makro", "familia": "Aceites", "precio": 8.5}
        ], ensure_ascii=False, indent=2), encoding="utf-8")

        gestor = GestorArticulos416(str(ruta_db))

        resultado = gestor.alta_articulo(
            nombre="Arroz bomba",
            proveedor="Makro",
            familia="Arroces",
            precio="3,20",
        )

        assert resultado.accion == "creado"
        assert resultado.codigo == "ART000002"

        articulos = json.loads(ruta_db.read_text(encoding="utf-8"))
        assert len(articulos) == 2
        assert articulos[1]["nombre"] == "Arroz bomba"
        assert articulos[1]["precio"] == 3.2

        duplicado = gestor.alta_articulo(nombre="Arroz bomba", proveedor="Makro")
        assert duplicado.accion == "no_creado"

    print("TEST OK - Host AI 4.1.6 Alta Manual de Artículos")
    print("Alta artículo: OK")
    print("Control duplicado: OK")


if __name__ == "__main__":
    main()
