from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Any


class ContextoGlobalRR161A:
    """Contexto operativo persistente y compartido por la consola Host AI.

    Guarda únicamente identificadores. Los objetos completos siguen viviendo en
    sus motores y bases correspondientes, evitando duplicar datos de negocio.
    """

    CAMPOS = {
        "evento_id",
        "plan_produccion_id",
        "necesidad_compra_id",
        "pedido_compra_id",
        "escandallo_id",
        "servicio_id",
        "pase_id",
    }

    def __init__(self, base_dir: str | Path | None):
        self._persistir = base_dir is not None
        self.base_dir = Path(base_dir) if base_dir is not None else Path.cwd()
        self.ruta = self.base_dir / "DATOS" / "contexto_global_rr161a.json"
        self._lock = RLock()
        self._datos: dict[str, Any] = {}
        if self._persistir:
            self._cargar()

    def _cargar(self) -> None:
        with self._lock:
            try:
                if self.ruta.exists():
                    datos = json.loads(self.ruta.read_text(encoding="utf-8"))
                    if isinstance(datos, dict):
                        self._datos = {k: v for k, v in datos.items() if k in self.CAMPOS}
            except (OSError, json.JSONDecodeError, TypeError):
                self._datos = {}

    def _guardar(self) -> None:
        if not self._persistir:
            return
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal = self.ruta.with_suffix(".tmp")
        temporal.write_text(
            json.dumps(self._datos, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporal.replace(self.ruta)

    def obtener(self, campo: str, defecto: Any = None) -> Any:
        if campo not in self.CAMPOS:
            raise KeyError(f"Campo de contexto no permitido: {campo}")
        with self._lock:
            return self._datos.get(campo, defecto)

    def establecer(self, campo: str, valor: Any) -> Any:
        if campo not in self.CAMPOS:
            raise KeyError(f"Campo de contexto no permitido: {campo}")
        with self._lock:
            if valor in (None, ""):
                self._datos.pop(campo, None)
            else:
                self._datos[campo] = str(valor)
            self._guardar()
            return valor

    def limpiar(self, *campos: str) -> None:
        with self._lock:
            objetivos = campos or tuple(self.CAMPOS)
            for campo in objetivos:
                if campo not in self.CAMPOS:
                    raise KeyError(f"Campo de contexto no permitido: {campo}")
                self._datos.pop(campo, None)
            self._guardar()

    def resumen(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._datos)
