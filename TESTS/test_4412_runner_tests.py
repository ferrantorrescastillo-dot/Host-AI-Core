from pathlib import Path
import sys
import tempfile

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.runner_tests_4412 import RunnerTests4412


def test_runner_descubre_y_ejecuta_bloque_recepcion():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        tests = base / "TESTS"
        tests.mkdir()
        (tests / "test_441_demo_ok.py").write_text("print('ok recepcion')\n", encoding="utf-8")
        (tests / "test_421_no_recepcion.py").write_text("print('proveedores')\n", encoding="utf-8")
        runner = RunnerTests4412(base)
        encontrados = runner.descubrir_tests("4")
        assert len(encontrados) == 1
        assert encontrados[0].name == "test_441_demo_ok.py"
        informe = runner.ejecutar_bloque("4")
        assert informe["total"] == 1
        assert informe["ok"] == 1
        assert informe["fail"] == 0


if __name__ == "__main__":
    test_runner_descubre_y_ejecuta_bloque_recepcion()
    print("OK test_4412_runner_tests")
