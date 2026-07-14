from pathlib import Path
from typing import Any, Dict, List

from SERVICIOS.mapa_maestro_modulos_4107 import generar_mapa_maestro

CARPETAS_CRITICAS = ["APP", "SERVICIOS", "MOTORES", "CORE", "MODELOS", "PIPELINES", "DATOS", "TESTS", "DOCS"]


def generar_cierre_tecnico_host_ai_4(raiz: str | Path = ".") -> Dict[str, Any]:
    raiz = Path(raiz)
    mapa = generar_mapa_maestro(raiz)
    carpetas = {}
    faltantes = []
    for carpeta in CARPETAS_CRITICAS:
        existe = (raiz / carpeta).exists()
        carpetas[carpeta] = existe
        if not existe:
            faltantes.append(carpeta)

    tests = list((raiz / "TESTS").glob("test_*.py")) if (raiz / "TESTS").exists() else []
    docs = list((raiz / "DOCS").glob("*.md")) if (raiz / "DOCS").exists() else []

    bloques = mapa.get("bloques", {})
    bloques_sin_archivos = [b for b, items in bloques.items() if not items]
    estado = "APTO_PARA_HOST_AI_5" if not faltantes and not bloques_sin_archivos else "REVISAR_ANTES_DE_HOST_AI_5"

    recomendaciones = []
    if mapa.get("historicos"):
        recomendaciones.append("Clasificar o archivar módulos históricos antes de diseñar la interfaz 5.0.")
    recomendaciones.append("No borrar APP/SERVICIOS duplicados sin revisar: muchos APP son wrappers válidos.")
    recomendaciones.append("El siguiente bloque recomendado es Host AI 5.1: interfaz principal conectada al Centro de Control y al Runner.")
    recomendaciones.append("Antes de vender beta, ejecutar runner completo y guardar informe de auditoría.")

    return {
        "raiz": str(raiz.resolve()),
        "estado": estado,
        "carpetas_criticas": carpetas,
        "carpetas_faltantes": faltantes,
        "total_tests": len(tests),
        "total_docs": len(docs),
        "bloques": {b: len(items) for b, items in bloques.items()},
        "bloques_sin_archivos": bloques_sin_archivos,
        "historicos": len(mapa.get("historicos", [])),
        "recomendaciones": recomendaciones,
    }


def formatear_cierre_tecnico(resultado: Dict[str, Any]) -> str:
    lineas: List[str] = []
    lineas.append("=== HOST AI 4.10.8 - CIERRE TECNICO HOST AI 4.0 ===")
    lineas.append(f"Raiz analizada: {resultado.get('raiz', '')}")
    lineas.append(f"Estado final: {resultado.get('estado', '')}")
    lineas.append("")
    lineas.append("Carpetas criticas:")
    for carpeta, existe in resultado.get("carpetas_criticas", {}).items():
        lineas.append(f"- {carpeta}: {'OK' if existe else 'FALTA'}")
    lineas.append("")
    lineas.append(f"Tests detectados: {resultado.get('total_tests', 0)}")
    lineas.append(f"Documentacion detectada: {resultado.get('total_docs', 0)}")
    lineas.append(f"Archivos historicos/sin bloque 4.x: {resultado.get('historicos', 0)}")
    lineas.append("")
    lineas.append("Cobertura por bloque:")
    for bloque, total in resultado.get("bloques", {}).items():
        lineas.append(f"- {bloque}: {total} archivos mapeados")
    if resultado.get("bloques_sin_archivos"):
        lineas.append("")
        lineas.append("Bloques sin archivos:")
        for bloque in resultado["bloques_sin_archivos"]:
            lineas.append(f"- {bloque}")
    lineas.append("")
    lineas.append("Conclusiones:")
    if resultado.get("estado") == "APTO_PARA_HOST_AI_5":
        lineas.append("- Host AI 4.0 queda tecnicamente cerrado y preparado para iniciar Host AI 5.0.")
    else:
        lineas.append("- Host AI 4.0 necesita revision antes de iniciar Host AI 5.0.")
    lineas.append("")
    lineas.append("Recomendaciones:")
    for rec in resultado.get("recomendaciones", []):
        lineas.append(f"- {rec}")
    return "\n".join(lineas)
