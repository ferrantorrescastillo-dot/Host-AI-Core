from pathlib import Path
import tempfile

from SERVICIOS.limpieza_apps_antiguas_4106 import analizar_apps_antiguas, formatear_limpieza_apps


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        (raiz / "APP").mkdir()
        (raiz / "SERVICIOS").mkdir()
        (raiz / "TESTS").mkdir()
        (raiz / "APP" / "modulo_demo_499.py").write_text("", encoding="utf-8")
        (raiz / "SERVICIOS" / "modulo_demo_499.py").write_text("", encoding="utf-8")
        (raiz / "TESTS" / "test_499_modulo_demo.py").write_text("", encoding="utf-8")
        (raiz / "APP" / "app_legacy_123.py").write_text("", encoding="utf-8")
        resultado = analizar_apps_antiguas(raiz)
        assert resultado["apps_total"] == 2
        assert "modulo_demo_499.py" in resultado["wrappers_validos"]
        assert "app_legacy_123.py" in resultado["apps_sin_servicio"]
        texto = formatear_limpieza_apps(resultado)
        assert "HOST AI 4.10.6" in texto
        assert "No borrar nada automaticamente" in texto
    print("OK test_4106_limpieza_apps_antiguas")


if __name__ == "__main__":
    main()
