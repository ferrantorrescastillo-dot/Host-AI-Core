from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.editor_articulos_417 import EditorArticulos417


def parsear_cambios(args):
    cambios = {}
    for arg in args:
        if "=" not in arg:
            continue
        clave, valor = arg.split("=", 1)
        cambios[clave.strip()] = valor.strip()
    return cambios


def main():
    if len(sys.argv) < 3:
        print("Uso:")
        print('python APP\\editar_articulo_417.py ART000355 precio=3,45 proveedor=Makro familia=Arroces')
        print('python APP\\editar_articulo_417.py "Arroz bomba" precio=3,45 proveedor=Makro')
        return

    identificador = sys.argv[1]
    cambios = parsear_cambios(sys.argv[2:])

    ruta_db = ROOT / "DATOS" / "db" / "articulos.json"
    editor = EditorArticulos417(str(ruta_db))

    if identificador.upper().startswith("ART"):
        resultado = editor.editar_por_codigo(identificador, **cambios)
    else:
        resultado = editor.editar_por_nombre(identificador, **cambios)

    print("HOST AI 4.1.7 - Edición de artículo")
    print("Encontrado:", resultado.encontrado)
    print("Actualizado:", resultado.actualizado)
    print("Código:", resultado.codigo or "-")
    print("Nombre:", resultado.nombre or "-")
    print("Mensaje:", resultado.mensaje)
    print("Campos actualizados:", resultado.campos_actualizados)


if __name__ == "__main__":
    main()
