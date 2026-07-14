from pathlib import Path
from SERVICIOS.auditoria_modulos_4101 import auditar_modulos, formatear_auditoria_modulos


def main():
    resultado = auditar_modulos(Path.cwd())
    texto = formatear_auditoria_modulos(resultado)
    assert "AUDITORIA GLOBAL DE MODULOS" in texto
    assert "APP" in resultado.carpetas_detectadas
    assert "TESTS" in resultado.carpetas_detectadas
    assert isinstance(resultado.conteo_archivos, dict)
    print(texto)
    print("\nOK test_4101_auditoria_modulos")


if __name__ == "__main__":
    main()
