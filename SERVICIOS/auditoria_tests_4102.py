from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Any
import py_compile

BLOQUES = {
    "4.1 Catalogo": "test_41",
    "4.2 Proveedores": "test_42",
    "4.3 Stock": "test_43",
    "4.4 Recepcion": "test_44",
    "4.5 Producto/Base": "test_45",
    "4.6 Produccion": "test_46",
    "4.7 Eventos": "test_47",
    "4.8 Rentabilidad": "test_48",
    "4.9 IA Operativa": "test_49",
}


@dataclass
class ResultadoAuditoriaTests:
    raiz: str
    total_tests: int
    tests_por_bloque: Dict[str, int]
    tests_sin_bloque: List[str]
    errores_compilacion: Dict[str, str]
    estado: str
    recomendaciones: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _tests(raiz: Path) -> List[Path]:
    carpeta = raiz / "TESTS"
    if not carpeta.exists():
        return []
    return sorted(p for p in carpeta.glob("test_*.py"))


def auditar_tests(raiz: str | Path = ".", compilar: bool = True) -> ResultadoAuditoriaTests:
    raiz = Path(raiz).resolve()
    archivos = _tests(raiz)
    tests_por_bloque = {bloque: 0 for bloque in BLOQUES}
    tests_sin_bloque: List[str] = []

    for test in archivos:
        asignado = False
        for bloque, prefijo in BLOQUES.items():
            if test.name.startswith(prefijo):
                tests_por_bloque[bloque] += 1
                asignado = True
                break
        if not asignado:
            tests_sin_bloque.append(test.name)

    errores_compilacion: Dict[str, str] = {}
    if compilar:
        for test in archivos:
            try:
                py_compile.compile(str(test), doraise=True)
            except Exception as exc:  # noqa: BLE001
                errores_compilacion[test.name] = str(exc)

    recomendaciones: List[str] = []
    if not archivos:
        recomendaciones.append("No se han encontrado tests. Revisar carpeta TESTS.")
    for bloque, total in tests_por_bloque.items():
        if total == 0:
            recomendaciones.append(f"El bloque {bloque} no tiene tests detectados por prefijo.")
    if errores_compilacion:
        recomendaciones.append("Corregir errores de compilacion antes de ejecutar bateria completa.")
    if tests_sin_bloque:
        recomendaciones.append("Clasificar tests historicos sin bloque 4.x para mejorar el runner.")
    if not recomendaciones:
        recomendaciones.append("La bateria de tests esta ordenada y compila correctamente.")

    estado = "OK" if archivos and not errores_compilacion else "REVISAR"
    return ResultadoAuditoriaTests(
        raiz=str(raiz),
        total_tests=len(archivos),
        tests_por_bloque=tests_por_bloque,
        tests_sin_bloque=tests_sin_bloque[:120],
        errores_compilacion=errores_compilacion,
        estado=estado,
        recomendaciones=recomendaciones,
    )


def formatear_auditoria_tests(resultado: ResultadoAuditoriaTests) -> str:
    lineas = ["=== HOST AI 4.10.2 - AUDITORIA GLOBAL DE TESTS ===", ""]
    lineas.append(f"Raiz analizada: {resultado.raiz}")
    lineas.append(f"Estado general: {resultado.estado}")
    lineas.append(f"Total tests detectados: {resultado.total_tests}")
    lineas.append("")
    lineas.append("Tests por bloque:")
    for bloque, total in resultado.tests_por_bloque.items():
        lineas.append(f"- {bloque}: {total}")
    lineas.append("")
    lineas.append(f"Tests historicos/sin bloque 4.x mostrados: {len(resultado.tests_sin_bloque)}")
    for item in resultado.tests_sin_bloque[:30]:
        lineas.append(f"  - {item}")
    lineas.append("")
    lineas.append(f"Errores de compilacion: {len(resultado.errores_compilacion)}")
    for nombre, error in list(resultado.errores_compilacion.items())[:10]:
        lineas.append(f"  - {nombre}: {error}")
    lineas.append("")
    lineas.append("Recomendaciones:")
    for rec in resultado.recomendaciones:
        lineas.append(f"- {rec}")
    return "\n".join(lineas)


if __name__ == "__main__":
    print(formatear_auditoria_tests(auditar_tests()))
