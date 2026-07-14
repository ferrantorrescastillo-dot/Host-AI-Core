from pathlib import Path
import importlib.util


def _cargar_modulo():
    ruta = Path(__file__).resolve().parents[1] / "ejecutar_certificacion_rr163.py"
    spec = importlib.util.spec_from_file_location("ejecutor_rr163", ruta)
    modulo = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(modulo)
    return modulo


def test_manifesto_controla_la_suite(tmp_path):
    modulo = _cargar_modulo()
    (tmp_path / "CERTIFICACION").mkdir()
    (tmp_path / "TESTS").mkdir()
    (tmp_path / "TESTS" / "test_oficial.py").write_text("def test_ok(): assert True\n", encoding="utf-8")
    (tmp_path / "CERTIFICACION" / "suite_oficial_rr163.txt").write_text(
        "# comentario\nTESTS/test_oficial.py\n", encoding="utf-8"
    )
    pruebas, errores = modulo._leer_suite(tmp_path)
    assert pruebas == ["TESTS/test_oficial.py"]
    assert errores == []


def test_manifesto_detecta_prueba_ausente(tmp_path):
    modulo = _cargar_modulo()
    (tmp_path / "CERTIFICACION").mkdir()
    (tmp_path / "CERTIFICACION" / "suite_oficial_rr163.txt").write_text(
        "TESTS/test_ausente.py\n", encoding="utf-8"
    )
    pruebas, errores = modulo._leer_suite(tmp_path)
    assert pruebas == []
    assert errores == ["Falta la prueba oficial: TESTS/test_ausente.py"]
