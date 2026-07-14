from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.gestor_articulos_416 import GestorArticulos416


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print('python APP\\alta_articulo_416.py "Arroz bomba" "Makro" "Arroces" "3,20"')
        return

    nombre = sys.argv[1]
    proveedor = sys.argv[2] if len(sys.argv) >= 3 else None
    familia = sys.argv[3] if len(sys.argv) >= 4 else None
    precio = sys.argv[4] if len(sys.argv) >= 5 else None

    ruta_db = ROOT / "DATOS" / "db" / "articulos.json"
    gestor = GestorArticulos416(str(ruta_db))

    resultado = gestor.alta_articulo(
        nombre=nombre,
        proveedor=proveedor,
        familia=familia,
        precio=precio,
    )

    print("HOST AI 4.1.6 - Alta de artículo")
    print("Acción:", resultado.accion)
    print("Código:", resultado.codigo)
    print("Nombre:", resultado.nombre)
    print("Base de datos:", resultado.ruta_db)
    print("Mensaje:", resultado.mensaje)


if __name__ == "__main__":
    main()
