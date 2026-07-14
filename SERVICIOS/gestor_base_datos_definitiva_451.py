from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List


class GestorBaseDatosDefinitiva451:
    """
    Host AI 4.5.1

    Crea y mantiene una base SQLite central para Host AI sin romper los JSON
    existentes. Corrección Windows: todas las conexiones SQLite se cierran
    explícitamente para que los tests temporales puedan borrar host_ai.db.
    """

    VERSION = "4.5.1"

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.db_dir = self.base_dir / "DATOS" / "db"
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.db_dir / "host_ai.db"

    def conectar(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        return con

    @contextmanager
    def conexion(self) -> Iterator[sqlite3.Connection]:
        con = self.conectar()
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def inicializar(self) -> Dict[str, Any]:
        tablas = self._crear_tablas()
        self._guardar_config("version_bd", self.VERSION)
        self._guardar_config("ultima_inicializacion", datetime.now().isoformat(timespec="seconds"))
        return {
            "ok": True,
            "version": self.VERSION,
            "db_path": str(self.db_path),
            "tablas_creadas_o_verificadas": tablas,
            "lectura_host_ai": f"Base de datos Host AI inicializada: {self.db_path.name}.",
        }

    def estado(self) -> Dict[str, Any]:
        if not self.db_path.exists():
            return {"ok": False, "existe": False, "tablas": [], "lectura_host_ai": "La base definitiva aún no existe."}
        with self.conexion() as con:
            tablas = [r["name"] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
            conteos = {}
            for tabla in tablas:
                if tabla.startswith("sqlite_"):
                    continue
                try:
                    conteos[tabla] = con.execute(f"SELECT COUNT(*) AS n FROM {tabla}").fetchone()["n"]
                except Exception:
                    conteos[tabla] = None
        return {
            "ok": True,
            "existe": True,
            "db_path": str(self.db_path),
            "tablas": tablas,
            "conteos": conteos,
            "lectura_host_ai": f"Base definitiva activa con {len(tablas)} tablas.",
        }

    def migrar_json_basico(self) -> Dict[str, Any]:
        self.inicializar()
        resumen = {"articulos": 0, "proveedores": 0, "avisos": []}
        articulos_path = self.db_dir / "articulos.json"
        proveedores_path = self.db_dir / "proveedores.json"

        with self.conexion() as con:
            if articulos_path.exists():
                try:
                    articulos = json.loads(articulos_path.read_text(encoding="utf-8"))
                    if isinstance(articulos, dict):
                        articulos = list(articulos.values())
                    for a in articulos:
                        if not isinstance(a, dict):
                            continue
                        codigo = str(a.get("codigo") or a.get("id") or a.get("articulo_id") or "").strip()
                        nombre = str(a.get("nombre") or a.get("articulo") or a.get("Artículo") or "").strip()
                        if not nombre:
                            continue
                        con.execute(
                            """
                            INSERT OR IGNORE INTO articulos
                            (codigo, nombre, familia, proveedor, unidad, precio, activo, origen)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                codigo or None,
                                nombre,
                                str(a.get("familia") or a.get("Familia") or ""),
                                str(a.get("proveedor") or a.get("Proveedor") or ""),
                                str(a.get("unidad") or a.get("unidad_base") or ""),
                                self._float_seguro(a.get("precio") or a.get("Precio") or a.get("precio_unitario")),
                                1 if a.get("activo", True) else 0,
                                "json_articulos",
                            ),
                        )
                        resumen["articulos"] += 1
                except Exception as exc:
                    resumen["avisos"].append(f"No se pudo migrar articulos.json: {exc}")

            if proveedores_path.exists():
                try:
                    proveedores = json.loads(proveedores_path.read_text(encoding="utf-8"))
                    if isinstance(proveedores, dict):
                        proveedores = list(proveedores.values())
                    for p in proveedores:
                        if not isinstance(p, dict):
                            continue
                        nombre = str(p.get("nombre") or p.get("proveedor") or p.get("Proveedor") or "").strip()
                        if not nombre:
                            continue
                        con.execute(
                            "INSERT OR IGNORE INTO proveedores (nombre, nif, telefono, email, activo, origen) VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                nombre,
                                str(p.get("nif") or p.get("cif") or ""),
                                str(p.get("telefono") or p.get("teléfono") or ""),
                                str(p.get("email") or ""),
                                1 if p.get("activo", True) else 0,
                                "json_proveedores",
                            ),
                        )
                        resumen["proveedores"] += 1
                except Exception as exc:
                    resumen["avisos"].append(f"No se pudo migrar proveedores.json: {exc}")

        resumen.update({
            "ok": True,
            "db_path": str(self.db_path),
            "lectura_host_ai": f"Migración básica preparada: {resumen['articulos']} artículos y {resumen['proveedores']} proveedores revisados.",
        })
        return resumen

    def _crear_tablas(self) -> List[str]:
        sentencias = {
            "restaurantes": """
                CREATE TABLE IF NOT EXISTS restaurantes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    slug TEXT NOT NULL UNIQUE,
                    tipo TEXT DEFAULT 'restaurante',
                    activo INTEGER DEFAULT 1,
                    creado_en TEXT NOT NULL
                )
            """,
            "articulos": """
                CREATE TABLE IF NOT EXISTS articulos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    restaurante_id INTEGER,
                    codigo TEXT UNIQUE,
                    nombre TEXT NOT NULL,
                    familia TEXT DEFAULT '',
                    proveedor TEXT DEFAULT '',
                    unidad TEXT DEFAULT '',
                    precio REAL DEFAULT 0,
                    stock_actual REAL DEFAULT 0,
                    stock_minimo REAL DEFAULT 0,
                    activo INTEGER DEFAULT 1,
                    origen TEXT DEFAULT '',
                    actualizado_en TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(restaurante_id) REFERENCES restaurantes(id)
                )
            """,
            "proveedores": """
                CREATE TABLE IF NOT EXISTS proveedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    restaurante_id INTEGER,
                    nombre TEXT NOT NULL,
                    nif TEXT DEFAULT '',
                    telefono TEXT DEFAULT '',
                    email TEXT DEFAULT '',
                    activo INTEGER DEFAULT 1,
                    origen TEXT DEFAULT '',
                    UNIQUE(restaurante_id, nombre),
                    FOREIGN KEY(restaurante_id) REFERENCES restaurantes(id)
                )
            """,
            "stock_movimientos": """
                CREATE TABLE IF NOT EXISTS stock_movimientos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    restaurante_id INTEGER,
                    articulo_id INTEGER,
                    tipo TEXT NOT NULL,
                    cantidad REAL NOT NULL,
                    unidad TEXT DEFAULT '',
                    proveedor TEXT DEFAULT '',
                    motivo TEXT DEFAULT '',
                    documento TEXT DEFAULT '',
                    creado_en TEXT NOT NULL,
                    FOREIGN KEY(restaurante_id) REFERENCES restaurantes(id),
                    FOREIGN KEY(articulo_id) REFERENCES articulos(id)
                )
            """,
            "pedidos": """
                CREATE TABLE IF NOT EXISTS pedidos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    restaurante_id INTEGER,
                    proveedor TEXT DEFAULT '',
                    estado TEXT DEFAULT 'borrador',
                    total REAL DEFAULT 0,
                    creado_en TEXT NOT NULL,
                    cerrado_en TEXT DEFAULT '',
                    FOREIGN KEY(restaurante_id) REFERENCES restaurantes(id)
                )
            """,
            "recepciones": """
                CREATE TABLE IF NOT EXISTS recepciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    restaurante_id INTEGER,
                    pedido_id INTEGER,
                    proveedor TEXT DEFAULT '',
                    documento TEXT DEFAULT '',
                    estado TEXT DEFAULT 'borrador',
                    resumen_json TEXT DEFAULT '{}',
                    creado_en TEXT NOT NULL,
                    cerrado_en TEXT DEFAULT '',
                    FOREIGN KEY(restaurante_id) REFERENCES restaurantes(id),
                    FOREIGN KEY(pedido_id) REFERENCES pedidos(id)
                )
            """,
            "historico_precios": """
                CREATE TABLE IF NOT EXISTS historico_precios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    restaurante_id INTEGER,
                    articulo_id INTEGER,
                    proveedor TEXT DEFAULT '',
                    precio REAL NOT NULL,
                    unidad TEXT DEFAULT '',
                    origen TEXT DEFAULT '',
                    creado_en TEXT NOT NULL,
                    FOREIGN KEY(restaurante_id) REFERENCES restaurantes(id),
                    FOREIGN KEY(articulo_id) REFERENCES articulos(id)
                )
            """,
            "configuracion": """
                CREATE TABLE IF NOT EXISTS configuracion (
                    clave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL,
                    actualizado_en TEXT NOT NULL
                )
            """,
            "logs_ejecucion": """
                CREATE TABLE IF NOT EXISTS logs_ejecucion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    modulo TEXT NOT NULL,
                    accion TEXT DEFAULT '',
                    ok INTEGER DEFAULT 1,
                    duracion_segundos REAL DEFAULT 0,
                    error TEXT DEFAULT '',
                    usuario TEXT DEFAULT '',
                    restaurante TEXT DEFAULT '',
                    creado_en TEXT NOT NULL
                )
            """,
        }
        with self.conexion() as con:
            for sql in sentencias.values():
                con.execute(sql)
        return list(sentencias.keys())

    def _guardar_config(self, clave: str, valor: str) -> None:
        with self.conexion() as con:
            con.execute(
                "INSERT OR REPLACE INTO configuracion (clave, valor, actualizado_en) VALUES (?, ?, ?)",
                (clave, str(valor), datetime.now().isoformat(timespec="seconds")),
            )

    @staticmethod
    def _float_seguro(valor: Any) -> float:
        try:
            if isinstance(valor, str):
                valor = valor.replace("€", "").replace(",", ".").strip()
            return float(valor or 0)
        except Exception:
            return 0.0


__all__ = ["GestorBaseDatosDefinitiva451"]
