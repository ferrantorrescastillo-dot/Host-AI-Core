from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

MANIFIESTO = Path("CERTIFICACION") / "suite_oficial_rr163.txt"
INFORME = Path("INFORME_RR1.6.3_ESTABILIZACION.md")


def _leer_suite(raiz: Path) -> tuple[list[str], list[str]]:
    manifiesto = raiz / MANIFIESTO
    if not manifiesto.exists():
        return [], [f"No existe el manifiesto oficial: {MANIFIESTO}"]

    pruebas: list[str] = []
    errores: list[str] = []
    for linea in manifiesto.read_text(encoding="utf-8").splitlines():
        limpia = linea.strip()
        if not limpia or limpia.startswith("#"):
            continue
        ruta = raiz / limpia
        if ruta.exists():
            pruebas.append(limpia)
        else:
            errores.append(f"Falta la prueba oficial: {limpia}")
    return pruebas, errores


def _guardar_informe(
    raiz: Path,
    estado: str,
    comando: list[str] | None,
    salida: str,
    incidencias: list[str],
) -> None:
    texto_incidencias = "\n".join(f"- {x}" for x in incidencias) or "- Ninguna"
    comando_txt = " ".join(comando) if comando else "No ejecutado"
    (raiz / INFORME).write_text(
        "# Informe RR1.6.3 — Limpieza y estabilización\n\n"
        f"- Fecha: {datetime.now().isoformat(timespec='seconds')}\n"
        f"- Estado: **{estado}**\n"
        f"- Comando: `{comando_txt}`\n"
        f"- Suite: `{MANIFIESTO.as_posix()}`\n\n"
        "## Incidencias de prevalidación\n\n"
        f"{texto_incidencias}\n\n"
        "## Resultado\n\n"
        "```text\n"
        f"{salida.strip()}\n"
        "```\n\n"
        "## Alcance\n\n"
        "Esta certificación ejecuta únicamente la suite oficial definida en el manifiesto. "
        "Los tests legacy permanecen intactos y no condicionan este resultado.\n",
        encoding="utf-8",
    )


def main() -> int:
    raiz = Path(__file__).resolve().parent
    incidencias: list[str] = []

    if importlib.util.find_spec("pytest") is None:
        incidencias.append("pytest no está instalado en este intérprete de Python.")
        salida = (
            "ERROR: falta pytest.\n"
            "Instálalo con:\n"
            f"  {sys.executable} -m pip install pytest"
        )
        _guardar_informe(raiz, "NO EJECUTADA", None, salida, incidencias)
        print(salida)
        print(f"\nInforme generado: {INFORME.name}")
        return 2

    pruebas, errores_suite = _leer_suite(raiz)
    incidencias.extend(errores_suite)
    if errores_suite or not pruebas:
        salida = "ERROR: la suite oficial no está completa; no se ejecutan pruebas parciales."
        _guardar_informe(raiz, "NO EJECUTADA", None, salida, incidencias)
        print(salida)
        for error in errores_suite:
            print(f"- {error}")
        print(f"\nInforme generado: {INFORME.name}")
        return 3

    env = os.environ.copy()
    env["PYTHONPATH"] = str(raiz) + os.pathsep + env.get("PYTHONPATH", "")
    comando = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-c",
        "pytest_rr163.ini",
        *pruebas,
    ]
    proceso = subprocess.run(
        comando,
        cwd=raiz,
        env=env,
        text=True,
        capture_output=True,
    )
    salida = (proceso.stdout or "") + ("\n" + proceso.stderr if proceso.stderr else "")
    estado = "APROBADA" if proceso.returncode == 0 else "NO APROBADA"
    _guardar_informe(raiz, estado, comando, salida, incidencias)

    print(salida.strip())
    print(f"\nEstado RR1.6.3: {estado}")
    print(f"Informe generado: {INFORME.name}")
    return proceso.returncode


if __name__ == "__main__":
    raise SystemExit(main())
