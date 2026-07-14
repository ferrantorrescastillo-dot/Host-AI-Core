from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from SERVICIOS.gestor_base_datos_definitiva_451 import GestorBaseDatosDefinitiva451


class GestorMultiRestaurante452:
    """
    Host AI 4.5.2

    Gestiona múltiples restaurantes sobre la base definitiva. Corrección Windows:
    usa el contexto `bd.conexion()` para cerrar SQLite explícitamente.
    """

    VERSION = "4.5.2"

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.bd = GestorBaseDatosDefinitiva451(self.base_dir)
        self.bd.inicializar()
        self.restaurantes_dir = self.base_dir / "Restaurantes"
        self.restaurantes_dir.mkdir(parents=True, exist_ok=True)

    def crear_restaurante(self, nombre: str, tipo: str = "restaurante") -> Dict[str, Any]:
        nombre = (nombre or "").strip()
        if not nombre:
            return {"ok": False, "error": "El nombre del restaurante es obligatorio.", "lectura_host_ai": "No se creó el restaurante: falta nombre."}
        slug = self._slug(nombre)
        creado_en = datetime.now().isoformat(timespec="seconds")
        with self.bd.conexion() as con:
            con.execute(
                "INSERT OR IGNORE INTO restaurantes (nombre, slug, tipo, activo, creado_en) VALUES (?, ?, ?, 1, ?)",
                (nombre, slug, tipo or "restaurante", creado_en),
            )
            fila = con.execute("SELECT * FROM restaurantes WHERE slug = ?", (slug,)).fetchone()
            restaurante = dict(fila) if fila else {}
        ruta = self._crear_estructura_restaurante(slug)
        return {
            "ok": True,
            "restaurante": restaurante,
            "ruta": str(ruta),
            "lectura_host_ai": f"Restaurante preparado: {nombre}.",
        }

    def listar_restaurantes(self) -> Dict[str, Any]:
        with self.bd.conexion() as con:
            filas = [dict(r) for r in con.execute("SELECT * FROM restaurantes ORDER BY nombre")]
            activo = self._obtener_config(con, "restaurante_activo_slug")
        return {
            "ok": True,
            "total": len(filas),
            "restaurante_activo_slug": activo,
            "restaurantes": filas,
            "lectura_host_ai": f"Restaurantes registrados: {len(filas)}.",
        }

    def seleccionar_restaurante(self, nombre_o_slug: str) -> Dict[str, Any]:
        clave = (nombre_o_slug or "").strip()
        if not clave:
            return {"ok": False, "error": "Indica nombre o slug.", "lectura_host_ai": "No se seleccionó restaurante."}
        slug = self._slug(clave)
        with self.bd.conexion() as con:
            fila = con.execute(
                "SELECT * FROM restaurantes WHERE slug = ? OR lower(nombre) = lower(?)",
                (slug, clave),
            ).fetchone()
            if not fila:
                return {"ok": False, "error": "Restaurante no encontrado.", "lectura_host_ai": f"No existe restaurante: {clave}."}
            restaurante = dict(fila)
            ahora = datetime.now().isoformat(timespec="seconds")
            con.execute("INSERT OR REPLACE INTO configuracion (clave, valor, actualizado_en) VALUES (?, ?, ?)", ("restaurante_activo_slug", restaurante["slug"], ahora))
            con.execute("INSERT OR REPLACE INTO configuracion (clave, valor, actualizado_en) VALUES (?, ?, ?)", ("restaurante_activo_nombre", restaurante["nombre"], ahora))
        return {"ok": True, "restaurante": restaurante, "lectura_host_ai": f"Restaurante activo: {restaurante['nombre']}."}

    def obtener_restaurante_activo(self) -> Dict[str, Any]:
        with self.bd.conexion() as con:
            slug = self._obtener_config(con, "restaurante_activo_slug")
            if not slug:
                return {"ok": False, "restaurante": None, "lectura_host_ai": "No hay restaurante activo."}
            fila = con.execute("SELECT * FROM restaurantes WHERE slug = ?", (slug,)).fetchone()
            restaurante = dict(fila) if fila else None
        if not restaurante:
            return {"ok": False, "restaurante": None, "lectura_host_ai": "El restaurante activo guardado ya no existe."}
        return {"ok": True, "restaurante": restaurante, "lectura_host_ai": f"Restaurante activo: {restaurante['nombre']}."}

    def ruta_restaurante_activo(self) -> Dict[str, Any]:
        activo = self.obtener_restaurante_activo()
        if not activo.get("ok"):
            return activo
        slug = activo["restaurante"]["slug"]
        ruta = self._crear_estructura_restaurante(slug)
        return {"ok": True, "ruta": str(ruta), "restaurante": activo["restaurante"], "lectura_host_ai": f"Ruta operativa activa: Restaurantes/{slug}."}

    def _crear_estructura_restaurante(self, slug: str) -> Path:
        ruta = self.restaurantes_dir / slug
        for sub in ["DATOS/db", "DOCUMENTOS", "LOGS", "EXPORTS"]:
            (ruta / sub).mkdir(parents=True, exist_ok=True)
        marcador = ruta / "README_RESTAURANTE.txt"
        if not marcador.exists():
            marcador.write_text(f"Restaurante Host AI: {slug}\nCreado para separar datos operativos.\n", encoding="utf-8")
        return ruta

    @staticmethod
    def _obtener_config(con: sqlite3.Connection, clave: str) -> str:
        fila = con.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,)).fetchone()
        return fila["valor"] if fila else ""

    @staticmethod
    def _slug(texto: str) -> str:
        texto = (texto or "").strip().lower()
        reemplazos = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n", "ç": "c"}
        for a, b in reemplazos.items():
            texto = texto.replace(a, b)
        texto = re.sub(r"[^a-z0-9]+", "_", texto).strip("_")
        return texto or "restaurante"


__all__ = ["GestorMultiRestaurante452"]
