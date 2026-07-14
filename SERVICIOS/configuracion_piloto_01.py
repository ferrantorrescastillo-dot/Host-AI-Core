from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json


@dataclass(frozen=True)
class RutasPiloto01:
    base_dir: str
    datos: str
    documentos: str
    logs: str
    backups: str
    certificaciones: str
    configuracion: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class ConfiguracionPiloto01:
    """Fuente única de rutas y configuración para la línea piloto.

    Reutiliza la configuración histórica si existe, pero normaliza todas las
    rutas respecto a la raíz oficial del proyecto. No contiene lógica de
    negocio ni modifica catálogos operativos.
    """

    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self.config_path = self.base_dir / "DATOS" / "configuracion" / "host_ai_config.json"

    def cargar(self) -> dict[str, Any]:
        base: dict[str, Any] = {
            "restaurante": "Restaurante Piloto",
            "ruta_datos": "DATOS",
            "ruta_documentos": "Documentos",
            "ruta_logs": "LOGS",
            "modo_entorno": "piloto",
            "ia_activa": False,
            "ocr_activo": False,
        }
        if self.config_path.exists():
            try:
                datos = json.loads(self.config_path.read_text(encoding="utf-8"))
                if isinstance(datos, dict):
                    base.update(datos)
            except (OSError, json.JSONDecodeError):
                base["configuracion_ilegible"] = True
        return base

    def rutas(self) -> RutasPiloto01:
        cfg = self.cargar()
        datos = self._resolver(cfg.get("ruta_datos", "DATOS"))
        documentos = self._resolver(cfg.get("ruta_documentos", "Documentos"))
        logs = self._resolver(cfg.get("ruta_logs", "LOGS"))
        return RutasPiloto01(
            base_dir=str(self.base_dir),
            datos=str(datos),
            documentos=str(documentos),
            logs=str(logs),
            backups=str(datos / "backups"),
            certificaciones=str(datos / "certificaciones" / "piloto01"),
            configuracion=str(self.config_path),
        )

    def validar(self) -> dict[str, Any]:
        cfg = self.cargar()
        rutas = self.rutas()
        errores: list[str] = []
        avisos: list[str] = []
        if cfg.get("configuracion_ilegible"):
            errores.append("La configuración central no se puede leer como JSON.")
        for campo in ("ruta_datos", "ruta_documentos", "ruta_logs"):
            if not str(cfg.get(campo, "")).strip():
                errores.append(f"{campo} está vacío.")
        if str(cfg.get("modo_entorno", "")).lower() not in {"piloto", "desarrollo", "produccion"}:
            avisos.append("modo_entorno no es un valor estándar.")
        return {
            "ok": not errores,
            "errores": errores,
            "avisos": avisos,
            "configuracion": cfg,
            "rutas": rutas.to_dict(),
        }

    def asegurar_rutas_no_operativas(self) -> list[str]:
        """Crea solo carpetas auxiliares del piloto, nunca catálogos de negocio."""
        rutas = self.rutas()
        creadas: list[str] = []
        for ruta_txt in (rutas.logs, rutas.certificaciones):
            ruta = Path(ruta_txt)
            ruta.mkdir(parents=True, exist_ok=True)
            creadas.append(str(ruta))
        return creadas

    def _resolver(self, valor: Any) -> Path:
        ruta = Path(str(valor or "").strip())
        return ruta.resolve() if ruta.is_absolute() else (self.base_dir / ruta).resolve()


__all__ = ["ConfiguracionPiloto01", "RutasPiloto01"]
