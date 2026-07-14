from __future__ import annotations

from dataclasses import dataclass, asdict
from importlib import import_module
from pathlib import Path
from typing import Any
import json
import sys

from SERVICIOS.configuracion_piloto_01 import ConfiguracionPiloto01


@dataclass(frozen=True)
class ComprobacionPiloto01:
    codigo: str
    ok: bool
    detalle: str
    severidad: str = "ERROR"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AuditorArranquePiloto01:
    MODULOS_CRITICOS = (
        "CORE.host_ai_core",
        "APP.consola",
        "SERVICIOS.host_ai_launcher",
        "SERVICIOS.configuracion_central_4414",
        "SERVICIOS.auditor_integridad_postimportacion_i1344",
        "SERVICIOS.motor_escritura_segura_i1342",
    )

    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self.config = ConfiguracionPiloto01(self.base_dir)

    def ejecutar(self, importar_modulos: bool = True) -> dict[str, Any]:
        comprobaciones: list[ComprobacionPiloto01] = []
        comprobaciones.append(ComprobacionPiloto01("PYTHON", sys.version_info >= (3, 11), sys.version.split()[0]))

        requeridos = {
            "MAIN": self.base_dir / "main.py",
            "APP": self.base_dir / "APP",
            "CORE": self.base_dir / "CORE",
            "SERVICIOS": self.base_dir / "SERVICIOS",
            "DATOS": self.base_dir / "DATOS",
            "CONSOLA": self.base_dir / "APP" / "consola.py",
            "CORE_PRINCIPAL": self.base_dir / "CORE" / "host_ai_core.py",
        }
        for codigo, ruta in requeridos.items():
            comprobaciones.append(ComprobacionPiloto01(codigo, ruta.exists(), str(ruta)))

        validacion_cfg = self.config.validar()
        comprobaciones.append(
            ComprobacionPiloto01(
                "CONFIGURACION",
                bool(validacion_cfg["ok"]),
                "; ".join(validacion_cfg["errores"] or ["Configuración válida"]),
            )
        )

        for nombre, ruta in self._catalogos_criticos().items():
            comprobaciones.append(self._validar_json(nombre, ruta))

        if importar_modulos:
            for modulo in self.MODULOS_CRITICOS:
                try:
                    import_module(modulo)
                    comprobaciones.append(ComprobacionPiloto01(f"IMPORT:{modulo}", True, "OK"))
                except Exception as exc:  # auditoría: debe informar cualquier error de importación
                    comprobaciones.append(ComprobacionPiloto01(f"IMPORT:{modulo}", False, repr(exc)))

        errores = [c for c in comprobaciones if not c.ok and c.severidad == "ERROR"]
        avisos = [c for c in comprobaciones if not c.ok and c.severidad == "AVISO"]
        estado = "LISTO_PARA_PILOTO" if not errores else "REVISAR_ANTES_DEL_PILOTO"
        return {
            "ok": not errores,
            "estado": estado,
            "base_dir": str(self.base_dir),
            "comprobaciones": [c.to_dict() for c in comprobaciones],
            "errores": len(errores),
            "avisos": len(avisos),
            "configuracion": validacion_cfg,
        }

    def _catalogos_criticos(self) -> dict[str, Path]:
        db = self.base_dir / "DATOS" / "db"
        candidatos = {
            "ARTICULOS": db / "articulos.json",
            "RECETAS": db / "escandallos.json",
            "MENUS": db / "menus.json",
        }
        return candidatos

    @staticmethod
    def _validar_json(nombre: str, ruta: Path) -> ComprobacionPiloto01:
        if not ruta.exists():
            return ComprobacionPiloto01(f"JSON:{nombre}", False, f"No existe: {ruta}", "AVISO")
        try:
            json.loads(ruta.read_text(encoding="utf-8"))
            return ComprobacionPiloto01(f"JSON:{nombre}", True, str(ruta))
        except (OSError, json.JSONDecodeError) as exc:
            return ComprobacionPiloto01(f"JSON:{nombre}", False, repr(exc))


__all__ = ["AuditorArranquePiloto01", "ComprobacionPiloto01"]
