import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.medidor_rendimiento_piloto import MedidorRendimientoPiloto


def funcion_rapida():
    return {"ok": True}


def funcion_con_error():
    raise ValueError("fallo controlado")


def main():
    medidor = MedidorRendimientoPiloto(limite_ok_ms=1000, limite_aviso_ms=2000)

    medicion = medidor.medir("funcion_rapida", funcion_rapida)

    assert medicion.estado == "ok"
    assert medicion.resultado == {"ok": True}
    assert medicion.tiempo_ms >= 0

    medicion_error = medidor.medir("funcion_con_error", funcion_con_error)

    assert medicion_error.estado == "error"
    assert medicion_error.resultado is None
    assert "fallo controlado" in medicion_error.mensaje

    resumen = medidor.resumen()

    assert resumen["total_mediciones"] == 2
    assert resumen["por_estado"]["ok"] == 1
    assert resumen["por_estado"]["error"] == 1
    assert resumen["estado_general"] == "error"

    print("TEST OK - Host AI RC3.2 Rendimiento para Piloto")
    print("Mediciones:", resumen["total_mediciones"])
    print("Estado general:", resumen["estado_general"])


if __name__ == "__main__":
    main()
