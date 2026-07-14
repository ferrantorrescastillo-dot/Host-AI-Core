from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


class LectorModeloCanonico555B72:
    """Lector compatible del catálogo de recetas de Host AI.

    Prioridad:
    1. ``DATOS/db/escandallos_canonicos.json`` (modelo 5.5.5A/5.5.5B).
    2. ``DATOS/db/escandallos.json`` (compatibilidad con el modelo anterior).

    El servicio es estrictamente de solo lectura. Nunca crea, actualiza ni
    reescribe archivos durante una consulta conversacional.
    """

    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        self.db_dir = self.base_dir / "DATOS" / "db"
        self.ruta_canonica = self.db_dir / "escandallos_canonicos.json"
        self.ruta_legacy = self.db_dir / "escandallos.json"

    def cargar(self) -> Dict[str, Any]:
        canonicos = self._cargar_canonicos(self.ruta_canonica)
        if canonicos:
            return {
                "escandallos": canonicos,
                "fuente": str(self.ruta_canonica.relative_to(self.base_dir)),
                "modelo": "CANONICO_5.5.5A",
                "solo_lectura": True,
                "errores": [],
            }

        legacy = self._cargar_legacy(self.ruta_legacy)
        if legacy:
            return {
                "escandallos": legacy,
                "fuente": str(self.ruta_legacy.relative_to(self.base_dir)),
                "modelo": "LEGACY_COMPATIBLE",
                "solo_lectura": True,
                "errores": [],
            }

        return {
            "escandallos": [],
            "fuente": str(self.ruta_canonica.relative_to(self.base_dir)),
            "modelo": "SIN_DATOS",
            "solo_lectura": True,
            "errores": [],
        }

    @staticmethod
    def _leer_json(path: Path) -> Any:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _cargar_canonicos(self, path: Path) -> List[Dict[str, Any]]:
        data = self._leer_json(path)
        if not isinstance(data, dict):
            return []
        registros = data.get("escandallos")
        if not isinstance(registros, list):
            return []
        normalizados: List[Dict[str, Any]] = []
        for item in registros:
            if not isinstance(item, dict):
                continue
            receta = item.get("receta") if isinstance(item.get("receta"), dict) else {}
            nombre = str(receta.get("nombre") or "").strip()
            if not nombre:
                continue
            ingredientes = receta.get("ingredientes") if isinstance(receta.get("ingredientes"), list) else []
            normalizados.append(
                {
                    "codigo": receta.get("codigo", ""),
                    "nombre": nombre,
                    "receta": nombre,
                    "rendimiento": receta.get("rendimiento", 0),
                    "unidad_rendimiento": receta.get("unidad_rendimiento", ""),
                    "ingredientes": [x for x in ingredientes if isinstance(x, dict)],
                    "coste_total": item.get("coste_total", 0),
                    "precio_venta_unitario": item.get("precio_venta_unitario", receta.get("precio_venta_unitario")),
                    "precio_venta": item.get("precio_venta", receta.get("precio_venta")),
                    "pvp": item.get("pvp", receta.get("pvp")),
                    "iva_pct": item.get("iva_pct", receta.get("iva_pct")),
                    "origen_modelo": "canonico",
                    "raw": item,
                }
            )
        return normalizados

    def _cargar_legacy(self, path: Path) -> List[Dict[str, Any]]:
        data = self._leer_json(path)
        if isinstance(data, list):
            registros = data
        elif isinstance(data, dict):
            registros = next(
                (data[k] for k in ("escandallos", "recetas", "items") if isinstance(data.get(k), list)),
                [],
            )
        else:
            registros = []
        return [x for x in registros if isinstance(x, dict)]
