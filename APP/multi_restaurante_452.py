from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.gestor_multi_restaurante_452 import GestorMultiRestaurante452


def main():
    gestor = GestorMultiRestaurante452(ROOT)
    while True:
        print("\n=== HOST AI 4.5.2 - MULTI RESTAURANTE ===")
        print("1. Listar restaurantes")
        print("2. Crear restaurante")
        print("3. Seleccionar restaurante activo")
        print("4. Ver restaurante activo")
        print("0. Salir")
        op = input("Selecciona: ").strip()
        if op == "0":
            break
        if op == "1":
            res = gestor.listar_restaurantes()
            print(res["lectura_host_ai"])
            for r in res["restaurantes"]:
                marca = "*" if r["slug"] == res.get("restaurante_activo_slug") else " "
                print(f"{marca} {r['nombre']} ({r['slug']})")
        elif op == "2":
            nombre = input("Nombre restaurante: ").strip()
            tipo = input("Tipo [restaurante/hotel/catering]: ").strip() or "restaurante"
            print(gestor.crear_restaurante(nombre, tipo).get("lectura_host_ai"))
        elif op == "3":
            clave = input("Nombre o slug: ").strip()
            print(gestor.seleccionar_restaurante(clave).get("lectura_host_ai"))
        elif op == "4":
            print(gestor.obtener_restaurante_activo().get("lectura_host_ai"))
        else:
            print("Opción no válida.")


if __name__ == "__main__":
    main()
