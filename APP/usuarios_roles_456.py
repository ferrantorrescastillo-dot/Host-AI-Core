from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.gestor_usuarios_roles_456 import GestorUsuariosRoles456


def main() -> None:
    gestor = GestorUsuariosRoles456(ROOT)
    while True:
        print("\n=== HOST AI 4.5.6 - USUARIOS Y ROLES ===")
        print("1. Listar roles")
        print("2. Listar usuarios")
        print("3. Crear usuario")
        print("4. Cambiar rol")
        print("0. Salir")
        opcion = input("Selecciona: ").strip()
        if opcion == "1":
            print(gestor.listar_roles())
        elif opcion == "2":
            print(gestor.listar_usuarios())
        elif opcion == "3":
            nombre = input("Nombre: ").strip()
            email = input("Email: ").strip()
            rol = input("Rol (admin/gerente/jefe_cocina/compras/cocinero): ").strip() or "cocinero"
            print(gestor.crear_usuario(nombre, email, rol))
        elif opcion == "4":
            email = input("Email: ").strip()
            rol = input("Nuevo rol: ").strip()
            print(gestor.cambiar_rol(email, rol))
        elif opcion == "0":
            break
        else:
            print("Opción no válida.")


if __name__ == "__main__":
    main()
