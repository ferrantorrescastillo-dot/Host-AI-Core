from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

try:
    from SERVICIOS.gestor_base_datos_definitiva_451 import GestorBaseDatosDefinitiva451
except Exception:  # pragma: no cover
    GestorBaseDatosDefinitiva451 = None  # type: ignore


class PanelEstadoHostAI455:
    """Host AI 4.5.5 - Panel de estado general del sistema."""

    VERSION = "4.5.5"

    def __init__(self, base_dir: str | Path = "."):
        self.base_dir = Path(base_dir)

    def generar_estado(self) -> Dict[str, Any]:
        datos_dir = self.base_dir / "DATOS"
        db_dir = datos_dir / "db"
        docs_dir = self.base_dir / "DOCS"
        tests_dir = self.base_dir / "TESTS"
        app_dir = self.base_dir / "APP"
        servicios_dir = self.base_dir / "SERVICIOS"
        logs_dir = self.base_dir / "LOGS"
        config_path = datos_dir / "config" / "host_ai_config.json"

        estado_bd: Dict[str, Any] = {"ok": False, "lectura_host_ai": "Gestor BD no disponible."}
        if GestorBaseDatosDefinitiva451 is not None:
            try:
                bd = GestorBaseDatosDefinitiva451(self.base_dir)
                bd.inicializar()
                estado_bd = bd.estado()
            except Exception as exc:
                estado_bd = {"ok": False, "error": str(exc), "lectura_host_ai": "No se pudo leer la base de datos."}

        config = self._leer_json(config_path)
        restaurante = self._restaurante_activo(estado_bd, config)

        resumen = {
            "ok": True,
            "version": self.VERSION,
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "restaurante_activo": restaurante,
            "rutas": {
                "APP": app_dir.exists(),
                "SERVICIOS": servicios_dir.exists(),
                "TESTS": tests_dir.exists(),
                "DATOS": datos_dir.exists(),
                "DOCS": docs_dir.exists(),
                "LOGS": logs_dir.exists(),
            },
            "conteos": {
                "apps": self._contar_py(app_dir),
                "servicios": self._contar_py(servicios_dir),
                "tests": len(list(tests_dir.glob("test_*.py"))) if tests_dir.exists() else 0,
                "docs": len(list(docs_dir.glob("*.md"))) if docs_dir.exists() else 0,
            },
            "base_datos": estado_bd,
            "configuracion": {
                "existe": config_path.exists(),
                "ruta": str(config_path),
                "restaurante": config.get("restaurante") if isinstance(config, dict) else None,
                "moneda": config.get("moneda") if isinstance(config, dict) else None,
                "idioma": config.get("idioma") if isinstance(config, dict) else None,
            },
        }
        resumen["lectura_host_ai"] = self._crear_lectura(resumen)
        return resumen

    def imprimir_estado(self) -> Dict[str, Any]:
        estado = self.generar_estado()
        print("=" * 48)
        print("HOST AI - PANEL DE ESTADO 4.5.5")
        print("=" * 48)
        print(f"Restaurante activo: {estado['restaurante_activo'] or 'No seleccionado'}")
        print(f"Tests detectados:    {estado['conteos']['tests']}")
        print(f"Apps detectadas:     {estado['conteos']['apps']}")
        print(f"Servicios detectados:{estado['conteos']['servicios']}")
        print(f"Base de datos:       {'OK' if estado['base_datos'].get('ok') else 'REVISAR'}")
        print("-" * 48)
        print(estado["lectura_host_ai"])
        return estado

    def _restaurante_activo(self, estado_bd: Dict[str, Any], config: Dict[str, Any]) -> str:
        try:
            conteos = estado_bd.get("conteos") or {}
            if conteos.get("restaurantes", 0) == 1:
                return "1 restaurante registrado"
            if conteos.get("restaurantes", 0) > 1:
                return f"{conteos['restaurantes']} restaurantes registrados"
        except Exception:
            pass
        if isinstance(config, dict):
            restaurante = config.get("restaurante") or config.get("restaurante_activo")
            if isinstance(restaurante, dict):
                return restaurante.get("nombre", "")
            if restaurante:
                return str(restaurante)
        return ""

    @staticmethod
    def _contar_py(ruta: Path) -> int:
        return len([p for p in ruta.glob("*.py") if p.name != "__init__.py"]) if ruta.exists() else 0

    @staticmethod
    def _leer_json(path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _crear_lectura(estado: Dict[str, Any]) -> str:
        bd_txt = "activa" if estado["base_datos"].get("ok") else "pendiente de revisar"
        return (
            f"Host AI operativo. Base de datos {bd_txt}. "
            f"Detectados {estado['conteos']['tests']} tests, "
            f"{estado['conteos']['apps']} apps y {estado['conteos']['servicios']} servicios."
        )


__all__ = ["PanelEstadoHostAI455"]
