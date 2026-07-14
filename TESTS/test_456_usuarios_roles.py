from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.gestor_usuarios_roles_456 import GestorUsuariosRoles456


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        gestor = GestorUsuariosRoles456(Path(tmpdir))
        roles = gestor.listar_roles()
        assert roles["ok"] is True
        assert roles["total"] >= 5

        creado = gestor.crear_usuario("Ferran", "ferran@test.com", "admin", "1234")
        assert creado["ok"] is True
        assert creado["usuario"]["email"] == "ferran@test.com"
        assert "password_hash" not in creado["usuario"]

        cambio = gestor.cambiar_rol("ferran@test.com", "jefe_cocina")
        assert cambio["ok"] is True

        usuarios = gestor.listar_usuarios()
        assert usuarios["total"] == 1
        assert usuarios["usuarios"][0]["rol"] == "jefe_cocina"

        baja = gestor.desactivar_usuario("ferran@test.com")
        assert baja["ok"] is True
        activos = gestor.listar_usuarios()
        assert activos["total"] == 0

    print("TEST OK 4.5.6 - Usuarios y roles")


if __name__ == "__main__":
    main()
