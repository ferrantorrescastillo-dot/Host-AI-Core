from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Any

CARPETAS_CLAVE = ["APP", "SERVICIOS", "MOTORES", "CORE", "MODELOS", "PIPELINES", "DATOS", "TESTS", "DOCS"]
CARPETAS_CODIGO = ["APP", "SERVICIOS", "MOTORES", "CORE", "MODELOS", "PIPELINES"]


@dataclass
class ResultadoAuditoriaModulos:
    raiz: str
    carpetas_detectadas: Dict[str, bool]
    conteo_archivos: Dict[str, int]
    modulos_app_sin_servicio_parecido: List[str]
    servicios_sin_test_parecido: List[str]
    posibles_duplicados: Dict[str, List[str]]
    estado: str
    recomendaciones: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _normalizar_nombre(nombre: str) -> str:
    limpio = nombre.lower().replace(".py", "")
    partes = [p for p in limpio.split("_") if not p.isdigit() and not p.startswith("4")]
    return "_".join(partes) or limpio


def _archivos_py(carpeta: Path) -> List[Path]:
    if not carpeta.exists():
        return []
    return sorted(p for p in carpeta.glob("*.py") if p.name != "__init__.py")


def _existe_parecido(nombre: str, candidatos: List[Path]) -> bool:
    base = _normalizar_nombre(nombre)
    if not base:
        return False
    for candidato in candidatos:
        cand = _normalizar_nombre(candidato.name)
        if base in cand or cand in base:
            return True
    return False


def auditar_modulos(raiz: str | Path = ".") -> ResultadoAuditoriaModulos:
    raiz = Path(raiz).resolve()
    carpetas_detectadas = {c: (raiz / c).exists() for c in CARPETAS_CLAVE}
    conteo_archivos = {}
    for c in CARPETAS_CLAVE:
        carpeta = raiz / c
        conteo_archivos[c] = len([p for p in carpeta.rglob("*") if p.is_file()]) if carpeta.exists() else 0

    apps = _archivos_py(raiz / "APP")
    servicios = _archivos_py(raiz / "SERVICIOS")
    tests = _archivos_py(raiz / "TESTS")

    app_sin_servicio = [p.name for p in apps if not _existe_parecido(p.name, servicios)]
    servicios_sin_test = [p.name for p in servicios if not _existe_parecido(p.name, tests)]

    nombres_por_base: Dict[str, List[str]] = {}
    for carpeta in CARPETAS_CODIGO:
        for archivo in _archivos_py(raiz / carpeta):
            base = _normalizar_nombre(archivo.name)
            nombres_por_base.setdefault(base, []).append(str(archivo.relative_to(raiz)))
    posibles_duplicados = {k: v for k, v in nombres_por_base.items() if len(v) > 1 and k not in {"", "main"}}

    recomendaciones: List[str] = []
    if not all(carpetas_detectadas.values()):
        recomendaciones.append("Crear o recuperar las carpetas clave que falten antes de avanzar a Host AI 5.0.")
    if app_sin_servicio:
        recomendaciones.append("Revisar APPs sin servicio parecido: pueden ser wrappers antiguos o módulos pendientes de conectar.")
    if servicios_sin_test:
        recomendaciones.append("Añadir tests a servicios sin prueba parecida para subir estabilidad.")
    if posibles_duplicados:
        recomendaciones.append("Revisar posibles duplicidades antes de crear interfaz 5.0.")
    if not recomendaciones:
        recomendaciones.append("La estructura principal parece coherente para continuar con auditorías más profundas.")

    estado = "OK" if all(carpetas_detectadas.values()) else "REVISAR"
    return ResultadoAuditoriaModulos(
        raiz=str(raiz),
        carpetas_detectadas=carpetas_detectadas,
        conteo_archivos=conteo_archivos,
        modulos_app_sin_servicio_parecido=app_sin_servicio,
        servicios_sin_test_parecido=servicios_sin_test[:100],
        posibles_duplicados=posibles_duplicados,
        estado=estado,
        recomendaciones=recomendaciones,
    )


def formatear_auditoria_modulos(resultado: ResultadoAuditoriaModulos) -> str:
    lineas = ["=== HOST AI 4.10.1 - AUDITORIA GLOBAL DE MODULOS ===", ""]
    lineas.append(f"Raiz analizada: {resultado.raiz}")
    lineas.append(f"Estado general: {resultado.estado}")
    lineas.append("")
    lineas.append("Carpetas clave:")
    for carpeta, existe in resultado.carpetas_detectadas.items():
        marca = "OK" if existe else "FALTA"
        lineas.append(f"- {carpeta}: {marca} ({resultado.conteo_archivos.get(carpeta, 0)} archivos)")
    lineas.append("")
    lineas.append(f"APP sin servicio parecido: {len(resultado.modulos_app_sin_servicio_parecido)}")
    for item in resultado.modulos_app_sin_servicio_parecido[:20]:
        lineas.append(f"  - {item}")
    lineas.append("")
    lineas.append(f"Servicios sin test parecido: {len(resultado.servicios_sin_test_parecido)} mostrados")
    for item in resultado.servicios_sin_test_parecido[:20]:
        lineas.append(f"  - {item}")
    lineas.append("")
    lineas.append(f"Posibles duplicidades: {len(resultado.posibles_duplicados)}")
    for base, archivos in list(resultado.posibles_duplicados.items())[:15]:
        lineas.append(f"  - {base}: {', '.join(archivos[:4])}")
    lineas.append("")
    lineas.append("Recomendaciones:")
    for rec in resultado.recomendaciones:
        lineas.append(f"- {rec}")
    return "\n".join(lineas)


if __name__ == "__main__":
    print(formatear_auditoria_modulos(auditar_modulos()))
