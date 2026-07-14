from pathlib import Path
import tempfile

from SERVICIOS.clasificador_tests_historicos_4105 import clasificar_test, clasificar_tests_historicos, formatear_clasificacion_tests


def main() -> None:
    assert clasificar_test("test_481_coste_real_receta.py") == "4.8 Rentabilidad"
    assert clasificar_test("test_495_asistente_urgencias.py") == "4.9 IA Operativa"
    assert clasificar_test("test_lector_facturas_con_ocr.py") == "4.4 Recepcion"

    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        tests = raiz / "TESTS"
        tests.mkdir()
        (tests / "test_481_coste_real_receta.py").write_text("print('ok')", encoding="utf-8")
        (tests / "test_lector_facturas_con_ocr.py").write_text("print('ok')", encoding="utf-8")
        (tests / "test_raro.py").write_text("print('ok')", encoding="utf-8")
        resultado = clasificar_tests_historicos(raiz)
        assert resultado["total_tests"] == 3
        assert "test_raro.py" in resultado["sin_clasificar"]
        texto = formatear_clasificacion_tests(resultado)
        assert "HOST AI 4.10.5" in texto
        assert "Tests sin clasificar: 1" in texto
    print("OK test_4105_clasificador_tests_historicos")


if __name__ == "__main__":
    main()
