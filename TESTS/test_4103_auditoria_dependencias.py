from pathlib import Path
from SERVICIOS.auditoria_dependencias_4103 import auditar_dependencias, formatear_auditoria_dependencias


def main():
    resultado = auditar_dependencias(Path.cwd())
    texto = formatear_auditoria_dependencias(resultado)
    assert "AUDITORIA DE IMPORTS Y DEPENDENCIAS" in texto
    assert resultado.total_archivos_python >= 1
    assert isinstance(resultado.imports_faltantes, int)
    assert isinstance(resultado.dependencias_por_carpeta, dict)
    print(texto)
    print("\nOK test_4103_auditoria_dependencias")


if __name__ == "__main__":
    main()
