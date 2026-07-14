import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.certificador_piloto_host_ai import CertificadorPilotoHostAI


def main():
    certificador = CertificadorPilotoHostAI()
    resultado = certificador.certificar(str(ROOT))

    resumen = resultado.resumen()

    assert resumen["estructura_carpetas"] == "OK"
    assert resumen["core"] == "OK"
    assert resumen["tests_criticos"] == "OK"
    assert resumen["servicios_rc3"] == "OK"

    assert resultado.estado_final in {
        CertificadorPilotoHostAI.ESTADO_APTO,
        CertificadorPilotoHostAI.ESTADO_OBSERVACIONES,
    }

    print("TEST OK - Host AI RC3.5 Certificación para Piloto")
    print("Versión:", resultado.version)
    print("Estado final:", resultado.estado_final)

    for criterio in resultado.criterios:
        print(f"{criterio.nombre}: {criterio.estado} - {criterio.mensaje}")
        for detalle in criterio.detalles:
            print(f"  - {detalle}")


if __name__ == "__main__":
    main()
