import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.editor_proveedores_422 import EditorProveedores422


def main():
    proveedores = [
        {
            "codigo": "PROV0001",
            "nombre": "MAKRO.",
            "nombre_normalizado": "makro",
            "articulos_asociados": 12,
            "variantes_detectadas": ["Makro", "MAKRO."],
            "estado": "activo",
            "observaciones": "Variantes detectadas.",
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta = Path(tmpdir) / "proveedores.json"
        ruta.write_text(json.dumps(proveedores, ensure_ascii=False, indent=2), encoding="utf-8")

        editor = EditorProveedores422(str(ruta))

        resultado = editor.editar_por_nombre("Makro", nombre="Makro", observaciones="Nombre oficial revisado.")
        assert resultado.encontrado is True
        assert resultado.actualizado is True
        assert resultado.nombre == "Makro"

        datos = json.loads(ruta.read_text(encoding="utf-8"))
        assert datos[0]["nombre"] == "Makro"
        assert datos[0]["nombre_normalizado"] == "makro"
        assert datos[0]["observaciones"] == "Nombre oficial revisado."

        no = editor.editar_por_codigo("PROV9999", nombre="No existe")
        assert no.encontrado is False

    print("TEST OK - Host AI 4.2.2 Editor de Proveedores")
    print("Edición proveedor: OK")
    print("No encontrado controlado: OK")


if __name__ == "__main__":
    main()
