import sys
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.verificador_instalacion_piloto import VerificadorInstalacionPiloto


def crear_estructura_minima(raiz: Path):
    for carpeta in VerificadorInstalacionPiloto.CARPETAS_OBLIGATORIAS:
        (raiz / carpeta).mkdir(parents=True, exist_ok=True)

    for archivo in VerificadorInstalacionPiloto.ARCHIVOS_OBLIGATORIOS:
        ruta = raiz / archivo
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text("# archivo de prueba\n", encoding="utf-8")


def main():
    verificador = VerificadorInstalacionPiloto()

    with tempfile.TemporaryDirectory() as tmpdir:
        raiz = Path(tmpdir)
        crear_estructura_minima(raiz)

        resultado = verificador.verificar(str(raiz))

        assert resultado.estado == "ok"
        assert resultado.es_valida is True
        assert not resultado.carpetas_faltantes
        assert not resultado.archivos_faltantes
        assert len(resultado.carpetas_ok) == len(VerificadorInstalacionPiloto.CARPETAS_OBLIGATORIAS)

    with tempfile.TemporaryDirectory() as tmpdir:
        raiz = Path(tmpdir)
        (raiz / "CORE").mkdir(parents=True, exist_ok=True)

        resultado = verificador.verificar(str(raiz))

        assert resultado.estado == "error"
        assert resultado.es_valida is False
        assert "APP" in resultado.carpetas_faltantes
        assert "TESTS/test_host_ai_3_0_stable.py" in resultado.archivos_faltantes

    print("TEST OK - Host AI RC3.4 Instalación y Arranque para Piloto")


if __name__ == "__main__":
    main()
