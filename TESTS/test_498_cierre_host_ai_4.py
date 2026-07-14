import tempfile
from pathlib import Path

from SERVICIOS.cierre_host_ai_4_498 import generar_cierre_host_ai_4, formatear_cierre_host_ai_4, BLOQUES_4X


def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        for archivos in BLOQUES_4X.values():
            for archivo in archivos:
                ruta = base / archivo
                ruta.parent.mkdir(parents=True, exist_ok=True)
                ruta.write_text("# test\n", encoding="utf-8")
        informe = generar_cierre_host_ai_4(base)
        assert informe["version"] == "Host AI 4.0"
        assert informe["bloques_pendientes"] == 0
        assert informe["estado"] == "listo_para_auditoria_final"
        texto = formatear_cierre_host_ai_4(informe)
        assert "CIERRE HOST AI 4.0" in texto
        assert "Bloques OK" in texto
    print("TEST OK 4.9.8 Cierre Host AI 4.0")


if __name__ == "__main__":
    main()
