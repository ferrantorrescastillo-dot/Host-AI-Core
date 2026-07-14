from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

try:
    from SERVICIOS.auditoria_modulos_4101 import auditar_modulos
except Exception:  # pragma: no cover
    auditar_modulos = None

try:
    from SERVICIOS.auditoria_tests_4102 import auditar_tests
except Exception:  # pragma: no cover
    auditar_tests = None

from SERVICIOS.auditoria_dependencias_4103 import auditar_dependencias


@dataclass
class ResultadoInformeFinalHostAI4104:
    version_funcional: str
    estado_general: str
    total_archivos_python: int
    total_tests: int
    imports_faltantes: int
    errores_sintaxis: int
    bloques_4x_detectados: List[str] = field(default_factory=list)
    recomendaciones: List[str] = field(default_factory=list)
    resumen_modulos: Dict[str, int] = field(default_factory=dict)


def _detectar_bloques_4x(base: Path) -> List[str]:
    bloques = set()
    for carpeta in ["APP", "SERVICIOS", "TESTS", "DOCS"]:
        ruta = base / carpeta
        if not ruta.exists():
            continue
        for archivo in ruta.iterdir():
            nombre = archivo.name.lower()
            if "410" in nombre:
                bloques.add("4.10 Auditoría final")
            elif "49" in nombre or "491" in nombre or "498" in nombre:
                bloques.add("4.9 IA operativa central")
            elif "48" in nombre:
                bloques.add("4.8 Costes y rentabilidad")
            elif "47" in nombre:
                bloques.add("4.7 Eventos y banquetes")
            elif "46" in nombre:
                bloques.add("4.6 Producción operativa")
            elif "45" in nombre:
                bloques.add("4.5 Infraestructura producto")
            elif "44" in nombre:
                bloques.add("4.4 Recepción inteligente")
            elif "43" in nombre:
                bloques.add("4.3 Stock")
            elif "42" in nombre:
                bloques.add("4.2 Proveedores")
            elif "41" in nombre:
                bloques.add("4.1 Catálogo")
    orden = [
        "4.1 Catálogo", "4.2 Proveedores", "4.3 Stock", "4.4 Recepción inteligente",
        "4.5 Infraestructura producto", "4.6 Producción operativa", "4.7 Eventos y banquetes",
        "4.8 Costes y rentabilidad", "4.9 IA operativa central", "4.10 Auditoría final",
    ]
    return [b for b in orden if b in bloques]


def generar_informe_final_host_ai(base_dir: Path | str = ".") -> ResultadoInformeFinalHostAI4104:
    base = Path(base_dir).resolve()
    deps = auditar_dependencias(base)

    total_tests = 0
    if auditar_tests is not None:
        try:
            total_tests = auditar_tests(base).total_tests
        except Exception:
            total_tests = len(list((base / "TESTS").glob("test_*.py"))) if (base / "TESTS").exists() else 0
    else:
        total_tests = len(list((base / "TESTS").glob("test_*.py"))) if (base / "TESTS").exists() else 0

    resumen_modulos: Dict[str, int] = {}
    if auditar_modulos is not None:
        try:
            resumen_modulos = dict(auditar_modulos(base).conteo_archivos)
        except Exception:
            resumen_modulos = {}
    if not resumen_modulos:
        for carpeta in ["APP", "SERVICIOS", "MOTORES", "CORE", "PIPELINES", "MODELOS", "TESTS", "DOCS"]:
            ruta = base / carpeta
            if ruta.exists():
                resumen_modulos[carpeta] = len([p for p in ruta.rglob("*.py") if "__pycache__" not in p.parts])

    recomendaciones: List[str] = []
    if deps.imports_faltantes:
        recomendaciones.append("Revisar imports internos faltantes antes de iniciar Host AI 5.0.")
    if deps.errores_sintaxis:
        recomendaciones.append("Corregir archivos con errores de sintaxis o lectura.")
    if total_tests == 0:
        recomendaciones.append("No se han detectado tests; revisar carpeta TESTS.")
    recomendaciones.append("Ejecutar el runner completo de tests antes de construir la interfaz Host AI 5.0.")
    recomendaciones.append("Mantener el desarrollo por parches pequeños para evitar duplicidades.")

    estado = "OK PARA PREPARAR HOST AI 5.0"
    if deps.imports_faltantes or deps.errores_sintaxis:
        estado = "REVISAR ANTES DE HOST AI 5.0"

    return ResultadoInformeFinalHostAI4104(
        version_funcional="Host AI 4.0",
        estado_general=estado,
        total_archivos_python=deps.total_archivos_python,
        total_tests=total_tests,
        imports_faltantes=deps.imports_faltantes,
        errores_sintaxis=len(deps.errores_sintaxis),
        bloques_4x_detectados=_detectar_bloques_4x(base),
        recomendaciones=recomendaciones,
        resumen_modulos=resumen_modulos,
    )


def formatear_informe_final_host_ai(informe: ResultadoInformeFinalHostAI4104) -> str:
    lineas = []
    lineas.append("=" * 60)
    lineas.append("HOST AI 4.10.4 - INFORME FINAL HOST AI 4.0")
    lineas.append("=" * 60)
    lineas.append(f"Versión funcional: {informe.version_funcional}")
    lineas.append(f"Estado general: {informe.estado_general}")
    lineas.append(f"Archivos Python auditados: {informe.total_archivos_python}")
    lineas.append(f"Tests detectados: {informe.total_tests}")
    lineas.append(f"Imports faltantes: {informe.imports_faltantes}")
    lineas.append(f"Errores sintaxis/lectura: {informe.errores_sintaxis}")
    lineas.append("")
    lineas.append("Bloques 4.x detectados:")
    for bloque in informe.bloques_4x_detectados:
        lineas.append(f"- {bloque}")
    lineas.append("")
    lineas.append("Resumen por carpeta:")
    for carpeta, total in sorted(informe.resumen_modulos.items()):
        lineas.append(f"- {carpeta}: {total}")
    lineas.append("")
    lineas.append("Recomendaciones:")
    for rec in informe.recomendaciones:
        lineas.append(f"- {rec}")
    return "\n".join(lineas)
