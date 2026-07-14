"""
Host AI - RC3.5 Certificación para Piloto

Certificador final de preparación para piloto real.

No modifica datos.
No ejecuta acciones de negocio.
Comprueba que la instalación contiene los elementos mínimos de RC3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class ResultadoCriterioPiloto:
    nombre: str
    estado: str
    mensaje: str
    detalles: List[str] = field(default_factory=list)


@dataclass
class ResultadoCertificacionPiloto:
    version: str
    estado_final: str
    criterios: List[ResultadoCriterioPiloto]

    @property
    def apto(self) -> bool:
        return self.estado_final == "APTO PARA PILOTO"

    def resumen(self) -> Dict[str, str]:
        return {criterio.nombre: criterio.estado for criterio in self.criterios}


class CertificadorPilotoHostAI:
    """
    Certifica si Host AI está preparado para una primera prueba piloto.

    Estados posibles:
    - APTO PARA PILOTO
    - APTO CON OBSERVACIONES
    - NO APTO
    """

    VERSION = "Host AI 3.0 RC3"
    ESTADO_APTO = "APTO PARA PILOTO"
    ESTADO_OBSERVACIONES = "APTO CON OBSERVACIONES"
    ESTADO_NO_APTO = "NO APTO"

    CARPETAS_MINIMAS = [
        "APP",
        "CORE",
        "MODELOS",
        "SERVICIOS",
        "PIPELINES",
        "TESTS",
        "DOCS",
        "DATOS",
    ]

    ARCHIVOS_CORE = [
        "CORE/host_ai_core.py",
        "CORE/orquestador.py",
        "CORE/registro_pipelines.py",
        "CORE/director_host_ai.py",
    ]

    TESTS_CRITICOS = [
        "TESTS/test_host_ai_3_0_stable.py",
        "TESTS/test_inteligencia_compras_3041_3042_3043_3044_3045_3046_3047_3048.py",
        "TESTS/test_gestion_inteligente_stock_3051_3052_3053_3054_3055_3056_3057_3058.py",
        "TESTS/test_produccion_3061_3062_3063_3064_3065_3066_3067_3068.py",
        "TESTS/test_escandallos_inteligentes_3071_3072_3073_3074_3075_3076_3077_3078.py",
        "TESTS/test_ia_conversacional_3081_3082_3083_3084_3085_3086_3087_3088.py",
    ]

    SERVICIOS_RC3 = [
        "SERVICIOS/validador_calidad_piloto.py",
        "SERVICIOS/medidor_rendimiento_piloto.py",
        "SERVICIOS/logger_piloto_host_ai.py",
        "SERVICIOS/verificador_instalacion_piloto.py",
        "SERVICIOS/certificador_piloto_host_ai.py",
    ]

    DOCS_MINIMOS = [
        "DOCS/RC3_1_CALIDAD_PILOTO.md",
        "DOCS/RC3_2_RENDIMIENTO_PILOTO.md",
        "DOCS/RC3_3_LOGS_PILOTO.md",
        "DOCS/RC3_4_INSTALACION_PILOTO.md",
        "DOCS/CERTIFICACION_RC3_PILOTO.md",
    ]

    def certificar(self, ruta_proyecto: str = ".") -> ResultadoCertificacionPiloto:
        raiz = Path(ruta_proyecto).resolve()

        criterios = [
            self._comprobar_carpetas(raiz),
            self._comprobar_core(raiz),
            self._comprobar_tests_criticos(raiz),
            self._comprobar_servicios_rc3(raiz),
            self._comprobar_docs(raiz),
            self._comprobar_logs(raiz),
            self._comprobar_version(raiz),
        ]

        estados = [criterio.estado for criterio in criterios]

        if "ERROR" in estados:
            estado_final = self.ESTADO_NO_APTO
        elif "AVISO" in estados:
            estado_final = self.ESTADO_OBSERVACIONES
        else:
            estado_final = self.ESTADO_APTO

        return ResultadoCertificacionPiloto(
            version=self.VERSION,
            estado_final=estado_final,
            criterios=criterios,
        )

    def _comprobar_carpetas(self, raiz: Path) -> ResultadoCriterioPiloto:
        faltantes = [carpeta for carpeta in self.CARPETAS_MINIMAS if not (raiz / carpeta).is_dir()]
        if faltantes:
            return ResultadoCriterioPiloto(
                nombre="estructura_carpetas",
                estado="ERROR",
                mensaje="Faltan carpetas obligatorias.",
                detalles=faltantes,
            )
        return ResultadoCriterioPiloto(
            nombre="estructura_carpetas",
            estado="OK",
            mensaje="Estructura mínima presente.",
        )

    def _comprobar_core(self, raiz: Path) -> ResultadoCriterioPiloto:
        faltantes = [archivo for archivo in self.ARCHIVOS_CORE if not (raiz / archivo).is_file()]
        if faltantes:
            return ResultadoCriterioPiloto(
                nombre="core",
                estado="ERROR",
                mensaje="Faltan archivos críticos de CORE.",
                detalles=faltantes,
            )
        return ResultadoCriterioPiloto("core", "OK", "Archivos críticos de CORE presentes.")

    def _comprobar_tests_criticos(self, raiz: Path) -> ResultadoCriterioPiloto:
        faltantes = [archivo for archivo in self.TESTS_CRITICOS if not (raiz / archivo).is_file()]
        if faltantes:
            return ResultadoCriterioPiloto(
                nombre="tests_criticos",
                estado="ERROR",
                mensaje="Faltan tests críticos para certificar Host AI.",
                detalles=faltantes,
            )
        return ResultadoCriterioPiloto("tests_criticos", "OK", "Tests críticos presentes.")

    def _comprobar_servicios_rc3(self, raiz: Path) -> ResultadoCriterioPiloto:
        faltantes = [archivo for archivo in self.SERVICIOS_RC3 if not (raiz / archivo).is_file()]
        if faltantes:
            return ResultadoCriterioPiloto(
                nombre="servicios_rc3",
                estado="ERROR",
                mensaje="Faltan servicios RC3 necesarios para piloto.",
                detalles=faltantes,
            )
        return ResultadoCriterioPiloto("servicios_rc3", "OK", "Servicios RC3 presentes.")

    def _comprobar_docs(self, raiz: Path) -> ResultadoCriterioPiloto:
        faltantes = [archivo for archivo in self.DOCS_MINIMOS if not (raiz / archivo).is_file()]
        if faltantes:
            return ResultadoCriterioPiloto(
                nombre="documentacion",
                estado="AVISO",
                mensaje="Falta documentación recomendada para piloto.",
                detalles=faltantes,
            )
        return ResultadoCriterioPiloto("documentacion", "OK", "Documentación mínima presente.")

    def _comprobar_logs(self, raiz: Path) -> ResultadoCriterioPiloto:
        ruta_logs = raiz / "LOGS"
        if not ruta_logs.exists():
            return ResultadoCriterioPiloto(
                nombre="logs",
                estado="AVISO",
                mensaje="No existe carpeta LOGS. Se recomienda crearla antes del piloto.",
                detalles=["LOGS/"],
            )
        return ResultadoCriterioPiloto("logs", "OK", "Carpeta de logs presente.")

    def _comprobar_version(self, raiz: Path) -> ResultadoCriterioPiloto:
        ruta_version = raiz / "VERSION.txt"
        if not ruta_version.exists():
            return ResultadoCriterioPiloto(
                nombre="versionado",
                estado="AVISO",
                mensaje="No existe VERSION.txt. Se recomienda versionar la instalación piloto.",
                detalles=["VERSION.txt"],
            )

        contenido = ruta_version.read_text(encoding="utf-8", errors="ignore")
        if "3.0 RC3" not in contenido:
            return ResultadoCriterioPiloto(
                nombre="versionado",
                estado="AVISO",
                mensaje="VERSION.txt existe, pero no indica Host AI 3.0 RC3.",
                detalles=[contenido.strip()],
            )

        return ResultadoCriterioPiloto("versionado", "OK", "Versionado RC3 presente.")


__all__ = [
    "CertificadorPilotoHostAI",
    "ResultadoCertificacionPiloto",
    "ResultadoCriterioPiloto",
]
