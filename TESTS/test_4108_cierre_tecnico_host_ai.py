from pathlib import Path
import tempfile

from SERVICIOS.cierre_tecnico_host_ai_4108 import generar_cierre_tecnico_host_ai_4, formatear_cierre_tecnico


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        for carpeta in ["APP", "SERVICIOS", "MOTORES", "CORE", "MODELOS", "PIPELINES", "DATOS", "TESTS", "DOCS"]:
            (raiz / carpeta).mkdir()
        muestras = {
            "APP/catalogo_411.py": "",
            "APP/proveedor_421.py": "",
            "APP/stock_431.py": "",
            "APP/recepcion_441.py": "",
            "APP/base_451.py": "",
            "APP/produccion_461.py": "",
            "APP/evento_471.py": "",
            "APP/rentabilidad_481.py": "",
            "APP/ia_491.py": "",
            "APP/cierre_4108.py": "",
            "TESTS/test_4108_cierre_tecnico_host_ai.py": "",
            "DOCS/HOST_AI_TEST.md": "# test",
        }
        for rel, contenido in muestras.items():
            (raiz / rel).write_text(contenido, encoding="utf-8")
        resultado = generar_cierre_tecnico_host_ai_4(raiz)
        assert resultado["estado"] == "APTO_PARA_HOST_AI_5"
        assert resultado["total_tests"] == 1
        texto = formatear_cierre_tecnico(resultado)
        assert "HOST AI 4.10.8" in texto
        assert "APTO_PARA_HOST_AI_5" in texto
    print("OK test_4108_cierre_tecnico_host_ai")


if __name__ == "__main__":
    main()
