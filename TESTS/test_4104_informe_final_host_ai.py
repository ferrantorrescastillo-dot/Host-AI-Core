from pathlib import Path
from SERVICIOS.informe_final_host_ai_4104 import generar_informe_final_host_ai, formatear_informe_final_host_ai


def main():
    informe = generar_informe_final_host_ai(Path.cwd())
    texto = formatear_informe_final_host_ai(informe)
    assert "INFORME FINAL HOST AI 4.0" in texto
    assert informe.version_funcional == "Host AI 4.0"
    assert informe.total_archivos_python >= 1
    assert isinstance(informe.recomendaciones, list)
    print(texto)
    print("\nOK test_4104_informe_final_host_ai")


if __name__ == "__main__":
    main()
