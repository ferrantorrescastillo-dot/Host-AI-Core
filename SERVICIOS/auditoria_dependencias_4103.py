from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple

CARPETAS_INTERNAS = {"APP", "SERVICIOS", "MOTORES", "CORE", "PIPELINES", "MODELOS", "DATOS", "TESTS"}
CARPETAS_AUDITADAS = ["APP", "SERVICIOS", "MOTORES", "CORE", "PIPELINES", "MODELOS", "TESTS"]


@dataclass
class ImportInterno:
    archivo: str
    modulo: str
    existe: bool


@dataclass
class ResultadoAuditoriaDependencias4103:
    total_archivos_python: int = 0
    total_imports_internos: int = 0
    imports_ok: int = 0
    imports_faltantes: int = 0
    errores_sintaxis: List[str] = field(default_factory=list)
    imports: List[ImportInterno] = field(default_factory=list)
    dependencias_por_carpeta: Dict[str, int] = field(default_factory=dict)
    estado: str = "PENDIENTE"


def _modulo_a_ruta(base: Path, modulo: str) -> bool:
    partes = modulo.split(".")
    if not partes:
        return False
    ruta_py = base.joinpath(*partes).with_suffix(".py")
    ruta_pkg = base.joinpath(*partes, "__init__.py")
    return ruta_py.exists() or ruta_pkg.exists()


def _extraer_imports(path: Path) -> Set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    encontrados: Set[str] = set()
    for nodo in ast.walk(tree):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                encontrados.add(alias.name)
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.module:
                encontrados.add(nodo.module)
    return encontrados


def auditar_dependencias(base_dir: Path | str = ".") -> ResultadoAuditoriaDependencias4103:
    base = Path(base_dir).resolve()
    resultado = ResultadoAuditoriaDependencias4103()

    archivos: List[Path] = []
    for carpeta in CARPETAS_AUDITADAS:
        ruta = base / carpeta
        if ruta.exists():
            archivos.extend(p for p in ruta.rglob("*.py") if "__pycache__" not in p.parts)

    resultado.total_archivos_python = len(archivos)
    vistos: Set[Tuple[str, str]] = set()

    for archivo in archivos:
        carpeta_raiz = archivo.relative_to(base).parts[0]
        resultado.dependencias_por_carpeta.setdefault(carpeta_raiz, 0)
        try:
            imports = _extraer_imports(archivo)
        except SyntaxError as exc:
            resultado.errores_sintaxis.append(f"{archivo.relative_to(base)} -> {exc}")
            continue
        except UnicodeDecodeError as exc:
            resultado.errores_sintaxis.append(f"{archivo.relative_to(base)} -> error lectura: {exc}")
            continue

        for modulo in sorted(imports):
            raiz = modulo.split(".")[0]
            if raiz not in CARPETAS_INTERNAS:
                continue
            clave = (str(archivo.relative_to(base)), modulo)
            if clave in vistos:
                continue
            vistos.add(clave)
            existe = _modulo_a_ruta(base, modulo)
            resultado.imports.append(ImportInterno(str(archivo.relative_to(base)), modulo, existe))
            resultado.total_imports_internos += 1
            resultado.dependencias_por_carpeta[carpeta_raiz] += 1
            if existe:
                resultado.imports_ok += 1
            else:
                resultado.imports_faltantes += 1

    if resultado.errores_sintaxis or resultado.imports_faltantes:
        resultado.estado = "REVISAR"
    else:
        resultado.estado = "OK"
    return resultado


def formatear_auditoria_dependencias(resultado: ResultadoAuditoriaDependencias4103) -> str:
    lineas = []
    lineas.append("=" * 60)
    lineas.append("HOST AI 4.10.3 - AUDITORIA DE IMPORTS Y DEPENDENCIAS")
    lineas.append("=" * 60)
    lineas.append(f"Estado: {resultado.estado}")
    lineas.append(f"Archivos Python auditados: {resultado.total_archivos_python}")
    lineas.append(f"Imports internos detectados: {resultado.total_imports_internos}")
    lineas.append(f"Imports OK: {resultado.imports_ok}")
    lineas.append(f"Imports faltantes: {resultado.imports_faltantes}")
    lineas.append(f"Errores de sintaxis/lectura: {len(resultado.errores_sintaxis)}")
    lineas.append("")
    lineas.append("Dependencias por carpeta:")
    for carpeta, total in sorted(resultado.dependencias_por_carpeta.items()):
        lineas.append(f"- {carpeta}: {total}")

    faltantes = [i for i in resultado.imports if not i.existe]
    if faltantes:
        lineas.append("")
        lineas.append("Imports internos faltantes:")
        for item in faltantes[:50]:
            lineas.append(f"- {item.archivo} -> {item.modulo}")
        if len(faltantes) > 50:
            lineas.append(f"... y {len(faltantes)-50} más")

    if resultado.errores_sintaxis:
        lineas.append("")
        lineas.append("Errores de sintaxis/lectura:")
        for err in resultado.errores_sintaxis[:50]:
            lineas.append(f"- {err}")
    return "\n".join(lineas)
