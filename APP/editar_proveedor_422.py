from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.editor_proveedores_422 import EditorProveedores422


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
        print('python APP\\editar_proveedor_422.py PROV0001 nombre=Makro observaciones="Nombre oficial"')
        print('python APP\\editar_proveedor_422.py Makro nombre=Makro estado=activo')
        return

    identificador = sys.argv[1]
    cambios = parsear_cambios(sys.argv[2:])

    ruta = ROOT / "DATOS" / "db" / "proveedores.json"
    editor = EditorProveedores422(str(ruta))

    if identificador.upper().startswith("PROV"):
        resultado = editor.editar_por_codigo(identificador, **cambios)
    else:
        resultado = editor.editar_por_nombre(identificador, **cambios)

    print("HOST AI 4.2.2 - Editor de Proveedores")
    print("Encontrado:", resultado.encontrado)
    print("Actualizado:", resultado.actualizado)
    print("Código:", resultado.codigo or "-")
    print("Nombre:", resultado.nombre or "-")
    print("Mensaje:", resultado.mensaje)
    print("Campos actualizados:", resultado.campos_actualizados)


if __name__ == "__main__":
    main()
