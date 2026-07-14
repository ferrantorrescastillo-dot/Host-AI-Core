from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.editor_familias_articulos_4111 import EditorFamiliasArticulos4111


def main():
    if len(sys.argv) < 3:
        print("Uso:")
        print('python APP\\asignar_familia_4111.py ART000123 "Varios"')
        print('python APP\\asignar_familia_4111.py "Arroz bomba" "Arroces y cereales"')
        return

    identificador = sys.argv[1]
    familia = sys.argv[2]

    ruta_db = ROOT / "DATOS" / "db" / "articulos.json"
    editor = EditorFamiliasArticulos4111(str(ruta_db))

    if identificador.upper().startswith("ART"):
        resultado = editor.asignar_por_codigo(identificador, familia)
    else:
        resultado = editor.asignar_por_nombre(identificador, familia)

    print("HOST AI 4.1.11 - Editor Manual de Familias")
    print("Encontrado:", resultado.encontrado)
    print("Actualizado:", resultado.actualizado)
    print("Código:", resultado.codigo or "-")
    print("Nombre:", resultado.nombre or "-")
    print("Familia anterior:", resultado.familia_anterior or "-")
    print("Familia nueva:", resultado.familia_nueva or "-")
    print("Mensaje:", resultado.mensaje)


if __name__ == "__main__":
    main()
