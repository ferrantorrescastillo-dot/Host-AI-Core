from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from SERVICIOS.modelo_flujo_operativo import cargar_flujo_json, guardar_flujo_json


class RepositorioFlujosJSON:
    """Persistencia JSON de flujos operativos en modo seguro."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self.flows_dir = self.base_dir / "DATOS" / "flujos"

    def ruta_flujo(self, id_flujo: str) -> Path:
        return self.flows_dir / f"{str(id_flujo or '').strip()}.json"

    def guardar(self, flujo: Dict[str, Any], ruta: Optional[Path] = None, overwrite: bool = False) -> Dict[str, Any]:
        destino = Path(ruta).resolve() if ruta else self.ruta_flujo(str(flujo.get("id_flujo") or ""))
        return guardar_flujo_json(flujo, ruta=destino, base_dir=self.base_dir, overwrite=overwrite)

    def cargar(self, ruta: Optional[Path] = None, id_flujo: Optional[str] = None) -> Dict[str, Any]:
        if ruta is None:
            if not id_flujo:
                return {
                    "ok": False,
                    "estado": "carga_error",
                    "mensaje": "Debes indicar ruta o id_flujo para cargar.",
                    "flujo": None,
                }
            ruta = self.ruta_flujo(id_flujo)
        return cargar_flujo_json(Path(ruta))


__all__ = ["RepositorioFlujosJSON"]
