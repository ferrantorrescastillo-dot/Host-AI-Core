from __future__ import annotations

"""
Host AI 4.4.15 - Instalación automática local.

Prepara carpetas mínimas, configuración central y archivos .gitkeep sin tocar la lógica
existente del proyecto. Pensado para facilitar pruebas y futuras instalaciones en restaurantes.
"""

from pathlib import Path
from typing import Any, Dict, List
import sys

try:
    from SERVICIOS.configuracion_central_4414 import GestorConfiguracionCentral4414
except ModuleNotFoundError:  # permite ejecución directa desde APP/ o TESTS/
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from SERVICIOS.configuracion_central_4414 import GestorConfiguracionCentral4414


class InstaladorHostAI4415:
    """Instalador seguro: crea estructura, no borra datos y no sobrescribe módulos."""

    CARPETAS_BASE = [
        "APP",
        "CORE",
        "DATOS",
        "DATOS/db",
        "DATOS/configuracion",
        "DOCS",
        "Documentos",
        "LOGS",
        "MODELOS",
        "MOTORES",
        "PIPELINES",
        "Restaurantes",
        "SERVICIOS",
        "TESTS",
        "Version",
    ]

    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self.configuracion = GestorConfiguracionCentral4414(self.base_dir)

    def verificar_instalacion(self) -> Dict[str, Any]:
        faltantes = [carpeta for carpeta in self.CARPETAS_BASE if not (self.base_dir / carpeta).exists()]
        config_ok = self.configuracion.existe_configuracion()
        return {
            "ok": len(faltantes) == 0 and config_ok,
            "faltantes": faltantes,
            "configuracion_existe": config_ok,
            "base_dir": str(self.base_dir),
            "lectura_host_ai": "Instalación correcta." if len(faltantes) == 0 and config_ok else "Instalación incompleta. Ejecuta preparar_instalacion().",
        }

    def preparar_instalacion(self, restaurante: str | None = None) -> Dict[str, Any]:
        creadas: List[str] = []
        existentes: List[str] = []

        for carpeta in self.CARPETAS_BASE:
            ruta = self.base_dir / carpeta
            if ruta.exists():
                existentes.append(carpeta)
            else:
                ruta.mkdir(parents=True, exist_ok=True)
                creadas.append(carpeta)
            gitkeep = ruta / ".gitkeep"
            if ruta.is_dir() and not any(ruta.iterdir()):
                gitkeep.touch(exist_ok=True)

        config = self.configuracion.crear_si_no_existe()
        if restaurante:
            config = self.configuracion.actualizar_configuracion({"restaurante": restaurante})
        validacion = self.configuracion.validar_configuracion(config)
        self.configuracion.asegurar_rutas_configuradas()

        return {
            "ok": validacion["ok"],
            "carpetas_creadas": creadas,
            "carpetas_existentes": existentes,
            "configuracion": config,
            "validacion": validacion,
            "lectura_host_ai": f"Instalación preparada. Carpetas nuevas: {len(creadas)}. Configuración: {'OK' if validacion['ok'] else 'REVISAR'}.",
        }

    def crear_informe_instalacion(self, nombre: str = "informe_instalacion_4_4_15.txt") -> Dict[str, Any]:
        estado = self.verificar_instalacion()
        destino = self.base_dir / "LOGS" / nombre
        destino.parent.mkdir(parents=True, exist_ok=True)
        lineas = [
            "HOST AI 4.4.15 - INFORME DE INSTALACIÓN",
            "=" * 50,
            f"Base: {estado['base_dir']}",
            f"Estado: {'OK' if estado['ok'] else 'REVISAR'}",
            f"Configuración existe: {estado['configuracion_existe']}",
            f"Carpetas faltantes: {', '.join(estado['faltantes']) if estado['faltantes'] else 'Ninguna'}",
        ]
        destino.write_text("\n".join(lineas), encoding="utf-8")
        return {
            "ok": True,
            "archivo": str(destino),
            "estado": estado,
            "lectura_host_ai": f"Informe de instalación creado: {destino.name}.",
        }
