import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.editor_articulos_417 import EditorArticulos417


def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_db = Path(tmpdir) / "articulos.json"
        ruta_db.write_text(json.dumps([
            {
                "codigo": "ART000001",
                "nombre": "Arroz bomba",
                "proveedor": "Makro",
                "familia": "Arroces",
                "precio": 3.2,
                "observaciones": None,
                "activo": True,
            }
        ], ensure_ascii=False, indent=2), encoding="utf-8")

        editor = EditorArticulos417(str(ruta_db))

        resultado = editor.editar_por_codigo(
            "ART000001",
            precio="3,45",
            proveedor="MAKRO",
            familia="Arroces y cereales",
        )

        assert resultado.encontrado is True
        assert resultado.actualizado is True
        assert resultado.codigo == "ART000001"
        assert resultado.campos_actualizados["precio"] == 3.45

        articulos = json.loads(ruta_db.read_text(encoding="utf-8"))
        assert articulos[0]["precio"] == 3.45
        assert articulos[0]["proveedor"] == "MAKRO"
        assert articulos[0]["familia"] == "Arroces y cereales"

        no_encontrado = editor.editar_por_codigo("ART999999", precio="1")
        assert no_encontrado.encontrado is False

    print("TEST OK - Host AI 4.1.7 Editor de Artículos")
    print("Edición por código: OK")
    print("No encontrado controlado: OK")


if __name__ == "__main__":
    main()
