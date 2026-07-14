from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.gestor_usuarios_roles_456 import GestorUsuariosRoles456
from SERVICIOS.permisos_avanzados_458 import PermisosAvanzados458


def main() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        base = Path(tmpdir)
        usuarios = GestorUsuariosRoles456(base)
        usuarios.crear_usuario("Ferran", "ferran@test.com", "admin", "1234")
        usuarios.crear_usuario("Cocinero", "cocinero@test.com", "cocinero", "1234")
        permisos = PermisosAvanzados458(base)

        assert permisos.puede("admin", "configuracion.editar") is True
        assert permisos.puede("compras", "compras.crear_pedido") is True
        assert permisos.puede("cocinero", "configuracion.editar") is False

        ok_admin = permisos.verificar_permiso("ferran@test.com", "usuarios.crear")
        assert ok_admin["permitido"] is True

        no_cocinero = permisos.verificar_permiso("cocinero@test.com", "configuracion.editar")
        assert no_cocinero["permitido"] is False

        permisos.conceder_permiso_rol("cocinero", "configuracion.ver")
        assert permisos.puede("cocinero", "configuracion.ver") is True
        permisos.revocar_permiso_rol("cocinero", "configuracion.ver")
        assert permisos.puede("cocinero", "configuracion.ver") is False

    print("TEST OK 4.5.8 - Permisos avanzados")


if __name__ == "__main__":
    main()
