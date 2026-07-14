import sys
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.logger_piloto_host_ai import LoggerPilotoHostAI


def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_log = Path(tmpdir) / "host_ai_piloto_test.log"
        logger = LoggerPilotoHostAI(str(ruta_log))

        evento_info = logger.info(
            modulo="stock",
            accion="consulta_stock",
            mensaje="Consulta de stock ejecutada correctamente.",
            datos={"articulo": "aceite", "stock": 12.5},
        )

        evento_aviso = logger.aviso(
            modulo="escandallos",
            accion="validar_receta",
            mensaje="Receta con ingrediente sin precio.",
            datos={"receta": "paella"},
        )

        evento_error = logger.error(
            modulo="compras",
            accion="crear_pedido",
            mensaje="Proveedor no encontrado.",
            datos={"proveedor": "Proveedor Test"},
        )

        assert ruta_log.exists()
        assert evento_info.nivel == "INFO"
        assert evento_aviso.nivel == "AVISO"
        assert evento_error.nivel == "ERROR"

        eventos = logger.leer_eventos()
        assert len(eventos) == 3
        assert eventos[0]["modulo"] == "stock"
        assert eventos[1]["nivel"] == "AVISO"
        assert eventos[2]["accion"] == "crear_pedido"

        resumen = logger.resumen()
        assert resumen["INFO"] == 1
        assert resumen["AVISO"] == 1
        assert resumen["ERROR"] == 1

    print("TEST OK - Host AI RC3.3 Logs para Piloto")
    print("Eventos registrados:", 3)


if __name__ == "__main__":
    main()
