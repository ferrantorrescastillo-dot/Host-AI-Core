"""
Host AI - RC3.4 Instalación y Arranque para Piloto

Verificador ligero para comprobar que una instalación local de Host AI
tiene la estructura mínima necesaria antes de usarla en restaurante.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class ResultadoVerificacionInstalacion:
    ruta_proyecto: str
    estado: str
    carpetas_ok: List[str]
    carpetas_faltantes: List[str]
    archivos_ok: List[str]
    archivos_faltantes: List[str]
    avisos: List[str]

    @property
    def es_valida(self) -> bool:
        return self.estado == "ok"


class VerificadorInstalacionPiloto:
    """
    Comprueba si la instalación de Host AI está preparada para piloto.

    No modifica archivos.
    No instala dependencias.
    No ejecuta motores.
    Solo valida estructura mínima.
    """

    CARPETAS_OBLIGATORIAS = [
        "APP",
        "CORE",
        "MODELOS",
        "SERVICIOS",
        "PIPELINES",
        "TESTS",
        "DOCS",
        "DATOS",
    ]

    ARCHIVOS_OBLIGATORIOS = [
        "CORE/host_ai_core.py",
        "CORE/orquestador.py",
        "CORE/registro_pipelines.py",
        "TESTS/test_host_ai_3_0_stable.py",
    ]

    def verificar(self, ruta_proyecto: str = ".") -> ResultadoVerificacionInstalacion:
        raiz = Path(ruta_proyecto).resolve()

        carpetas_ok: List[str] = []
        carpetas_faltantes: List[str] = []
        archivos_ok: List[str] = []
        archivos_faltantes: List[str] = []
        avisos: List[str] = []

        for carpeta in self.CARPETAS_OBLIGATORIAS:
            if (raiz / carpeta).is_dir():
                carpetas_ok.append(carpeta)
            else:
                carpetas_faltantes.append(carpeta)

        for archivo in self.ARCHIVOS_OBLIGATORIOS:
            if (raiz / archivo).is_file():
                archivos_ok.append(archivo)
            else:
                archivos_faltantes.append(archivo)

        if (raiz / "__pycache__").exists():
            avisos.append("Existe __pycache__ en la raíz del proyecto. No bloquea, pero conviene limpiar antes de distribuir.")

        if carpetas_faltantes or archivos_faltantes:
            estado = "error"
        elif avisos:
            estado = "aviso"
        else:
            estado = "ok"

        return ResultadoVerificacionInstalacion(
            ruta_proyecto=str(raiz),
            estado=estado,
            carpetas_ok=carpetas_ok,
            carpetas_faltantes=carpetas_faltantes,
            archivos_ok=archivos_ok,
            archivos_faltantes=archivos_faltantes,
            avisos=avisos,
        )


__all__ = [
    "ResultadoVerificacionInstalacion",
    "VerificadorInstalacionPiloto",
]
