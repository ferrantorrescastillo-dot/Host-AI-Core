from __future__ import annotations

from SERVICIOS.permisos_avanzados_458 import PermisosAvanzados458


def main() -> None:
    permisos = PermisosAvanzados458()
    print("=== HOST AI 4.5.8 - PERMISOS AVANZADOS ===")
    for rol in permisos.PERMISOS_BASE:
        info = permisos.permisos_de_rol(rol)
        print(f"\n{rol}: {info['total']} permisos")
        print(", ".join(info["permisos"]))


if __name__ == "__main__":
    main()
