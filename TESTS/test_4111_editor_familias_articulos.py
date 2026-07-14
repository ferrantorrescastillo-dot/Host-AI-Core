import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.editor_familias_articulos_4111 import EditorFamiliasArticulos4111


def main():
    articulos = [
        {"codigo": "ART000001", "nombre": "Producto raro", "familia": ""},
        {"codigo": "ART000002", "nombre": "Arroz bomba", "familia": "Arroces"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_db = Path(tmpdir) / "articulos.json"
        ruta_db.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding="utf-8")

        editor = EditorFamiliasArticulos4111(str(ruta_db))

        resultado = editor.asignar_por_codigo("ART000001", "Varios")
        assert resultado.encontrado is True
        assert resultado.actualizado is True
        assert resultado.familia_nueva == "Varios"

        datos = json.loads(ruta_db.read_text(encoding="utf-8"))
        prod = next(a for a in datos if a["codigo"] == "ART000001")
        assert prod["familia"] == "Varios"
        assert prod["familia_asignada_manual"] is True

        resultado2 = editor.asignar_por_nombre("Arroz bomba", "Arroces y cereales")
        assert resultado2.encontrado is True
        assert resultado2.familia_anterior == "Arroces"
        assert resultado2.familia_nueva == "Arroces y cereales"

        no = editor.asignar_por_codigo("ART999999", "Varios")
        assert no.encontrado is False

    print("TEST OK - Host AI 4.1.11 Editor Manual de Familias")
    print("Asignación por código: OK")
    print("Asignación por nombre: OK")


if __name__ == "__main__":
    main()
