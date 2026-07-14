from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from SERVICIOS.gestor_base_datos_definitiva_451 import GestorBaseDatosDefinitiva451
from SERVICIOS.gestor_usuarios_roles_456 import GestorUsuariosRoles456


class PermisosAvanzados458:
    """Host AI 4.5.8 - Sistema de permisos por rol y módulo."""

    VERSION = "4.5.8"
    PERMISOS_BASE = {
        "admin": ["*"],
        "gerente": ["catalogo.ver", "stock.ver", "compras.*", "recepcion.*", "informes.*", "escandallos.ver", "configuracion.ver"],
        "jefe_cocina": ["catalogo.ver", "stock.*", "produccion.*", "recepcion.*", "escandallos.*", "compras.ver", "ia.operar"],
        "compras": ["proveedores.*", "compras.*", "recepcion.*", "stock.ver", "catalogo.ver", "precios.*"],
        "almacen": ["stock.*", "recepcion.*", "inventario.*", "catalogo.ver"],
        "cocinero": ["produccion.ver", "produccion.operar", "recetas.ver", "stock.ver", "ia.consultar"],
        "solo_lectura": ["catalogo.ver", "stock.ver", "compras.ver", "produccion.ver", "escandallos.ver", "informes.ver"],
    }

    def __init__(self, base_dir: str | Path = "."):
        self.base_dir = Path(base_dir)
        self.bd = GestorBaseDatosDefinitiva451(self.base_dir)
        self.bd.inicializar()
        self.usuarios = GestorUsuariosRoles456(self.base_dir)
        self.inicializar()

    def inicializar(self) -> Dict[str, Any]:
        with self.bd.conexion() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS permisos_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rol TEXT NOT NULL,
                    permiso TEXT NOT NULL,
                    activo INTEGER DEFAULT 1,
                    creado_en TEXT NOT NULL,
                    UNIQUE(rol, permiso)
                )
                """
            )
            ahora = datetime.now().isoformat(timespec="seconds")
            for rol, permisos in self.PERMISOS_BASE.items():
                con.execute(
                    "INSERT OR IGNORE INTO roles (nombre, descripcion, activo, creado_en) VALUES (?, ?, 1, ?)",
                    (rol, f"Rol Host AI: {rol}", ahora),
                )
                for permiso in permisos:
                    con.execute(
                        "INSERT OR IGNORE INTO permisos_roles (rol, permiso, activo, creado_en) VALUES (?, ?, 1, ?)",
                        (rol, permiso, ahora),
                    )
        return {"ok": True, "version": self.VERSION, "roles": list(self.PERMISOS_BASE), "lectura_host_ai": "Permisos avanzados preparados."}

    def permisos_de_rol(self, rol: str) -> Dict[str, Any]:
        rol = (rol or "").strip().lower()
        with self.bd.conexion() as con:
            permisos = [r["permiso"] for r in con.execute("SELECT permiso FROM permisos_roles WHERE rol = ? AND activo = 1 ORDER BY permiso", (rol,))]
        return {"ok": True, "rol": rol, "permisos": permisos, "total": len(permisos), "lectura_host_ai": f"Permisos del rol {rol}: {len(permisos)}."}

    def puede(self, rol: str, permiso: str) -> bool:
        rol = (rol or "").strip().lower()
        permiso = (permiso or "").strip().lower()
        if not rol or not permiso:
            return False
        permisos = self.permisos_de_rol(rol)["permisos"]
        if "*" in permisos or permiso in permisos:
            return True
        modulo = permiso.split(".", 1)[0]
        return f"{modulo}.*" in permisos

    def verificar_permiso(self, email: str, permiso: str) -> Dict[str, Any]:
        email = (email or "").strip().lower()
        with self.bd.conexion() as con:
            usuario = con.execute("SELECT nombre, email, rol, activo FROM usuarios WHERE email = ?", (email,)).fetchone()
        if not usuario:
            return {"ok": False, "permitido": False, "error": "Usuario no encontrado.", "lectura_host_ai": "Acceso denegado: usuario no encontrado."}
        if int(usuario["activo"] or 0) != 1:
            return {"ok": True, "permitido": False, "usuario": dict(usuario), "lectura_host_ai": "Acceso denegado: usuario inactivo."}
        permitido = self.puede(usuario["rol"], permiso)
        return {"ok": True, "permitido": permitido, "usuario": dict(usuario), "permiso": permiso, "lectura_host_ai": "Acceso permitido." if permitido else "Acceso denegado por permisos."}

    def conceder_permiso_rol(self, rol: str, permiso: str) -> Dict[str, Any]:
        rol = (rol or "").strip().lower()
        permiso = (permiso or "").strip().lower()
        if not rol or not permiso:
            return {"ok": False, "error": "Rol y permiso son obligatorios."}
        with self.bd.conexion() as con:
            con.execute(
                "INSERT OR IGNORE INTO permisos_roles (rol, permiso, activo, creado_en) VALUES (?, ?, 1, ?)",
                (rol, permiso, datetime.now().isoformat(timespec="seconds")),
            )
            con.execute("UPDATE permisos_roles SET activo = 1 WHERE rol = ? AND permiso = ?", (rol, permiso))
        return {"ok": True, "lectura_host_ai": f"Permiso concedido: {rol} -> {permiso}."}

    def revocar_permiso_rol(self, rol: str, permiso: str) -> Dict[str, Any]:
        rol = (rol or "").strip().lower()
        permiso = (permiso or "").strip().lower()
        with self.bd.conexion() as con:
            con.execute("UPDATE permisos_roles SET activo = 0 WHERE rol = ? AND permiso = ?", (rol, permiso))
        return {"ok": True, "lectura_host_ai": f"Permiso revocado: {rol} -> {permiso}."}


__all__ = ["PermisosAvanzados458"]
