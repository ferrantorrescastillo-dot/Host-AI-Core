from pathlib import Path
from SERVICIOS.auditoria_tests_4102 import auditar_tests, formatear_auditoria_tests


def main():
    resultado = auditar_tests(Path.cwd())
    texto = formatear_auditoria_tests(resultado)
    assert "AUDITORIA GLOBAL DE TESTS" in texto
    assert resultado.total_tests >= 0
    assert "4.9 IA Operativa" in resultado.tests_por_bloque
    print(texto)
    print("\nOK test_4102_auditoria_tests")


if __name__ == "__main__":
    main()
