from pathlib import Path
import tempfile

from SERVICIOS.bootloader_host_ai_502 import BootloaderHostAI502


def main():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        for carpeta in ["APP", "CORE", "SERVICIOS", "TESTS", "DOCS"]:
            (base / carpeta).mkdir(parents=True, exist_ok=True)
        (base / "main.py").write_text("print('host ai')", encoding="utf-8")

        boot = BootloaderHostAI502(base)
        estado = boot.validar_estructura()
        assert estado["ok"] is True
        assert estado["APP"] is True
        assert estado["SERVICIOS"] is True
        assert estado["main_py"] is True

        opciones = boot.obtener_opciones()
        codigos = {o["codigo"] for o in opciones}
        assert "1" in codigos
        assert "9" in codigos

        no_valida = boot.ejecutar_opcion("999")
        assert no_valida["ok"] is False

    print("TEST OK 5.0.2 Bootloader Host AI")


if __name__ == "__main__":
    main()
