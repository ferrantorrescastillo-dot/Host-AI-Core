from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class LogEjecucionHostAI:
    fecha: str
    modulo: str
    accion: str
    duracion_segundos: float
    ok: bool
    errores: List[str]
    usuario: str = "local"
    restaurante: str = "default"
    detalle: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RegistroLogsProyecto4413:
    """
    Host AI 4.4.13 - Logs del proyecto.

    Guarda cada ejecución importante en LOGS/host_ai_ejecuciones.jsonl.
    Formato JSON Lines: una ejecución por línea, fácil de leer y auditar.
    """

    VERSION = "4.4.13"

    def __init__(self, base_dir: str | Path, usuario: str = "local", restaurante: str = "default"):
        self.base_dir = Path(base_dir)
        self.usuario = usuario or "local"
        self.restaurante = restaurante or "default"
        self.logs_dir = self.base_dir / "LOGS"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.logs_dir / "host_ai_ejecuciones.jsonl"

    def registrar(
        self,
        modulo: str,
        accion: str,
        duracion_segundos: float = 0.0,
        ok: bool = True,
        errores: Optional[List[str]] = None,
        detalle: Optional[Dict[str, Any]] = None,
        usuario: Optional[str] = None,
        restaurante: Optional[str] = None,
    ) -> Dict[str, Any]:
        registro = LogEjecucionHostAI(
            fecha=datetime.now().isoformat(timespec="seconds"),
            modulo=modulo or "general",
            accion=accion or "ejecucion",
            duracion_segundos=round(float(duracion_segundos or 0.0), 3),
            ok=bool(ok),
            errores=list(errores or []),
            usuario=usuario or self.usuario,
            restaurante=restaurante or self.restaurante,
            detalle=detalle or {},
        )
        data = registro.to_dict()
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(data, ensure_ascii=False) + "\n")
        return data

    def listar(self, limite: int = 20, solo_errores: bool = False) -> List[Dict[str, Any]]:
        if not self.log_path.exists():
            return []
        registros: List[Dict[str, Any]] = []
        with self.log_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if solo_errores and item.get("ok", True):
                    continue
                registros.append(item)
        if limite and limite > 0:
            return registros[-limite:]
        return registros

    def resumen(self) -> Dict[str, Any]:
        registros = self.listar(limite=0)
        total = len(registros)
        ok = sum(1 for r in registros if r.get("ok"))
        fail = total - ok
        ultimos_errores = [r for r in registros if not r.get("ok")][-5:]
        return {
            "version": self.VERSION,
            "total_ejecuciones": total,
            "ok": ok,
            "fail": fail,
            "log_path": str(self.log_path),
            "ultimos_errores": ultimos_errores,
            "lectura_host_ai": f"Logs Host AI: {total} ejecuciones, {ok} OK, {fail} con error.",
        }
