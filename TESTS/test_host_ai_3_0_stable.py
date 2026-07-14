"""
HOST AI 3.0 STABLE CANDIDATE - S-002

Test global no interactivo para validar Host AI 3.0 antes de pruebas controladas
con restaurantes.

Este test ejecuta los bloques principales y añade S-002, que valida cierres sanos
para Stock y Escandallos, evitando confundir tests diagnósticos con readiness real.

Ejecutar desde la raíz del proyecto:
    python TESTS\test_host_ai_3_0_stable.py
"""
from pathlib import Path
import runpy
import sys
import traceback

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

TESTS_ESTABLES = [
    "test_inteligencia_compras_3041_3042_3043_3044_3045_3046_3047_3048.py",
    "test_s002_cierres_stock_escandallos.py",
    "test_produccion_3061_3062_3063_3064_3065_3066_3067_3068.py",
    "test_ia_conversacional_3081_3082_3083_3084_3085_3086_3087_3088.py",
]


def ejecutar_test(path_test: Path) -> None:
    if not path_test.exists():
        raise FileNotFoundError(f"No existe el test requerido: {path_test}")
    runpy.run_path(str(path_test), run_name="__main__")


def ejecutar_prueba() -> None:
    print("=== HOST AI 3.0 STABLE CANDIDATE S-002 ===")
    print(f"Proyecto: {BASE_DIR}")
    print("Validando bloques principales y cierres operativos...\n")

    errores = []
    for nombre_test in TESTS_ESTABLES:
        path_test = BASE_DIR / "TESTS" / nombre_test
        print(f"--- Ejecutando {nombre_test} ---")
        try:
            ejecutar_test(path_test)
            print(f"OK: {nombre_test}\n")
        except Exception as exc:
            errores.append((nombre_test, exc, traceback.format_exc()))
            print(f"ERROR: {nombre_test}: {exc}\n")

    if errores:
        print("=== RESULTADO: ERROR ===")
        for nombre_test, exc, tb in errores:
            print(f"\n[FALLO] {nombre_test}: {exc}")
            print(tb)
        raise AssertionError(f"Host AI 3.0 Stable Candidate S-002 falló en {len(errores)} bloque(s).")

    print("=== RESULTADO: OK ===")
    print("TEST OK - Host AI 3.0 Stable Candidate S-002")
    print("Bloques validados: Compras, Stock saneado, Escandallos saneado, Producción e IA Conversacional")


if __name__ == "__main__":
    ejecutar_prueba()
