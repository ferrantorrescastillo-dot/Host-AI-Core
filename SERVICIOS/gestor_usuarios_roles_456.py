from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from SERVICIOS.gestor_base_datos_definitiva_451 import GestorBaseDatosDefinitiva451


class GestorUsuariosRoles456:
    """Host AI 4.5.6 - Usuarios y roles básicos para preparar el producto multiusuario."""

    VERSION = "4.5.6"
    ROLES_BASE = {
        "admin": "Acceso completo al sistema.",
        "gerente": "Gestión económica, informes y compras.",
        "jefe_cocina": "Gestión operativa de cocina, stock, producción y recetas.",
        "compras": "Pedidos, proveedores, recepción y precios.",
        "cocinero": "Producción, fichas, stock operativo y tareas asignadas.",
    }

    def __init__(self, base_dir: str | Path = "."):
        self.base_dir = Path(base_dir)
        self.bd = GestorBaseDatosDefinitiva451(self.base_dir)
        self.bd.inicializar()
        self.inicializar()

    def inicializar(self) -> Dict[str, Any]:
        with self.bd.conexion() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    descripcion TEXT DEFAULT '',
                    activo INTEGER DEFAULT 1,
                    creado_en TEXT NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    restaurante_id INTEGER,
                    nombre TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    rol TEXT NOT NULL,
                    password_hash TEXT DEFAULT '',
                    activo INTEGER DEFAULT 1,
                    creado_en TEXT NOT NULL,
                    ultimo_acceso TEXT DEFAULT '',
                    FOREIGN KEY(restaurante_id) REFERENCES restaurantes(id)
                )
                """
            )
            ahora = datetime.now().isoformat(timespec="seconds")
            for rol, descripcion in self.ROLES_BASE.items():
                con.execute(
                    "INSERT OR IGNORE INTO roles (nombre, descripcion, activo, creado_en) VALUES (?, ?, 1, ?)",
                    (rol, descripcion, ahora),
                )
        return {"ok": True, "roles_base": list(self.ROLES_BASE), "lectura_host_ai": "Usuarios y roles preparados."}

    def crear_usuario(self, nombre: str, email: str, rol: str = "cocinero", password: str = "", restaurante_id: Optional[int] = None) -> Dict[str, Any]:
        nombre = (nombre or "").strip()
        email = (email or "").strip().lower()
        rol = (rol or "cocinero").strip().lower()
        if not nombre or not email:
            return {"ok": False, "error": "Nombre y email son obligatorios.", "lectura_host_ai": "No se creó el usuario: faltan datos."}
        if rol not in self.ROLES_BASE:
            return {"ok": False, "error": f"Rol no válido: {rol}", "roles_validos": list(self.ROLES_BASE), "lectura_host_ai": "No se creó el usuario: rol no válido."}
        ahora = datetime.now().isoformat(timespec="seconds")
        password_hash = self._hash_password(password) if password else ""
        with self.bd.conexion() as con:
            con.execute(
                """
                INSERT OR IGNORE INTO usuarios
                (restaurante_id, nombre, email, rol, password_hash, activo, creado_en)
                VALUES (?, ?, ?, ?, ?, 1, ?)
                """,
                (restaurante_id, nombre, email, rol, password_hash, ahora),
            )
            fila = con.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
        return {"ok": True, "usuario": self._limpiar_usuario(fila), "lectura_host_ai": f"Usuario preparado: {nombre} ({rol})."}

    def listar_usuarios(self, solo_activos: bool = True) -> Dict[str, Any]:
        sql = "SELECT * FROM usuarios"
        if solo_activos:
            sql += " WHERE activo = 1"
        sql += " ORDER BY rol, nombre"
        with self.bd.conexion() as con:
            usuarios = [self._limpiar_usuario(r) for r in con.execute(sql)]
        return {"ok": True, "total": len(usuarios), "usuarios": usuarios, "lectura_host_ai": f"Usuarios activos: {len(usuarios)}."}

    def cambiar_rol(self, email: str, nuevo_rol: str) -> Dict[str, Any]:
        email = (email or "").strip().lower()
        nuevo_rol = (nuevo_rol or "").strip().lower()
        if nuevo_rol not in self.ROLES_BASE:
            return {"ok": False, "error": "Rol no válido.", "roles_validos": list(self.ROLES_BASE)}
        with self.bd.conexion() as con:
            cur = con.execute("UPDATE usuarios SET rol = ? WHERE email = ?", (nuevo_rol, email))
            if cur.rowcount == 0:
                return {"ok": False, "error": "Usuario no encontrado.", "lectura_host_ai": f"No existe usuario con email {email}."}
        return {"ok": True, "lectura_host_ai": f"Rol actualizado: {email} ahora es {nuevo_rol}."}

    def desactivar_usuario(self, email: str) -> Dict[str, Any]:
        email = (email or "").strip().lower()
        with self.bd.conexion() as con:
            cur = con.execute("UPDATE usuarios SET activo = 0 WHERE email = ?", (email,))
            if cur.rowcount == 0:
                return {"ok": False, "error": "Usuario no encontrado."}
        return {"ok": True, "lectura_host_ai": f"Usuario desactivado: {email}."}

    def listar_roles(self) -> Dict[str, Any]:
        with self.bd.conexion() as con:
            roles = [dict(r) for r in con.execute("SELECT nombre, descripcion, activo FROM roles ORDER BY nombre")]
        return {"ok": True, "total": len(roles), "roles": roles, "lectura_host_ai": f"Roles disponibles: {len(roles)}."}

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @staticmethod
    def _limpiar_usuario(fila: sqlite3.Row | None) -> Dict[str, Any]:
        if not fila:
            return {}
        data = dict(fila)
        data.pop("password_hash", None)
        return data


__all__ = ["GestorUsuariosRoles456"]
