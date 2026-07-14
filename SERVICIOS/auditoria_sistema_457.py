from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from SERVICIOS.gestor_base_datos_definitiva_451 import GestorBaseDatosDefinitiva451


class AuditoriaSistema457:
    """Host AI 4.5.7 - Auditoría completa de acciones importantes del sistema."""

    VERSION = "4.5.7"

    def __init__(self, base_dir: str | Path = "."):
        self.base_dir = Path(base_dir)
        self.bd = GestorBaseDatosDefinitiva451(self.base_dir)
        self.bd.inicializar()
        self.inicializar()

    def inicializar(self) -> Dict[str, Any]:
        with self.bd.conexion() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS auditoria_acciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT DEFAULT '',
                    restaurante TEXT DEFAULT '',
                    restaurante_id INTEGER,
                    modulo TEXT NOT NULL,
                    accion TEXT NOT NULL,
                    entidad TEXT DEFAULT '',
                    entidad_id TEXT DEFAULT '',
                    valor_anterior_json TEXT DEFAULT '{}',
                    valor_nuevo_json TEXT DEFAULT '{}',
                    detalle TEXT DEFAULT '',
                    ok INTEGER DEFAULT 1,
                    error TEXT DEFAULT '',
                    creado_en TEXT NOT NULL
                )
                """
            )
        return {"ok": True, "version": self.VERSION, "lectura_host_ai": "Auditoría del sistema preparada."}

    def registrar_accion(
        self,
        modulo: str,
        accion: str,
        usuario: str = "",
        restaurante: str = "",
        restaurante_id: Optional[int] = None,
        entidad: str = "",
        entidad_id: str | int = "",
        valor_anterior: Optional[Dict[str, Any]] = None,
        valor_nuevo: Optional[Dict[str, Any]] = None,
        detalle: str = "",
        ok: bool = True,
        error: str = "",
    ) -> Dict[str, Any]:
        modulo = (modulo or "").strip()
        accion = (accion or "").strip()
        if not modulo or not accion:
            return {"ok": False, "error": "Módulo y acción son obligatorios.", "lectura_host_ai": "No se pudo registrar la auditoría: faltan datos."}
        creado_en = datetime.now().isoformat(timespec="seconds")
        with self.bd.conexion() as con:
            cur = con.execute(
                """
                INSERT INTO auditoria_acciones
                (usuario, restaurante, restaurante_id, modulo, accion, entidad, entidad_id,
                 valor_anterior_json, valor_nuevo_json, detalle, ok, error, creado_en)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    usuario,
                    restaurante,
                    restaurante_id,
                    modulo,
                    accion,
                    entidad,
                    str(entidad_id or ""),
                    json.dumps(valor_anterior or {}, ensure_ascii=False),
                    json.dumps(valor_nuevo or {}, ensure_ascii=False),
                    detalle,
                    1 if ok else 0,
                    error,
                    creado_en,
                ),
            )
            auditoria_id = cur.lastrowid
        return {"ok": True, "auditoria_id": auditoria_id, "creado_en": creado_en, "lectura_host_ai": f"Auditoría registrada: {modulo} / {accion}."}

    def listar_acciones(self, modulo: str = "", usuario: str = "", restaurante: str = "", limite: int = 50) -> Dict[str, Any]:
        filtros: List[str] = []
        params: List[Any] = []
        if modulo:
            filtros.append("modulo = ?")
            params.append(modulo)
        if usuario:
            filtros.append("usuario = ?")
            params.append(usuario)
        if restaurante:
            filtros.append("restaurante = ?")
            params.append(restaurante)
        sql = "SELECT * FROM auditoria_acciones"
        if filtros:
            sql += " WHERE " + " AND ".join(filtros)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(int(limite or 50))
        with self.bd.conexion() as con:
            filas = [self._fila_a_dict(r) for r in con.execute(sql, params)]
        return {"ok": True, "total": len(filas), "acciones": filas, "lectura_host_ai": f"Acciones de auditoría encontradas: {len(filas)}."}

    def resumen_auditoria(self) -> Dict[str, Any]:
        with self.bd.conexion() as con:
            total = con.execute("SELECT COUNT(*) AS n FROM auditoria_acciones").fetchone()["n"]
            errores = con.execute("SELECT COUNT(*) AS n FROM auditoria_acciones WHERE ok = 0").fetchone()["n"]
            por_modulo = [dict(r) for r in con.execute("SELECT modulo, COUNT(*) AS total FROM auditoria_acciones GROUP BY modulo ORDER BY total DESC")]
        return {"ok": True, "total": total, "errores": errores, "por_modulo": por_modulo, "lectura_host_ai": f"Auditoría: {total} acciones registradas, {errores} con error."}

    @staticmethod
    def _fila_a_dict(fila: Any) -> Dict[str, Any]:
        data = dict(fila)
        for clave in ("valor_anterior_json", "valor_nuevo_json"):
            try:
                data[clave.replace("_json", "")] = json.loads(data.get(clave) or "{}")
            except Exception:
                data[clave.replace("_json", "")] = {}
        return data


__all__ = ["AuditoriaSistema457"]
