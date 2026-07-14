from pathlib import Path
import sys
import tempfile

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.registro_logs_proyecto_4413 import RegistroLogsProyecto4413


def test_registro_logs_crea_y_resume():
    with tempfile.TemporaryDirectory() as tmp:
        logger = RegistroLogsProyecto4413(Path(tmp), usuario="test", restaurante="demo")
        logger.registrar("TESTS", "demo_ok", 0.1, True)
        logger.registrar("TESTS", "demo_fail", 0.2, False, errores=["error demo"])
        registros = logger.listar(limite=10)
        resumen = logger.resumen()
        assert len(registros) == 2
        assert resumen["total_ejecuciones"] == 2
        assert resumen["ok"] == 1
        assert resumen["fail"] == 1
        assert logger.log_path.exists()


if __name__ == "__main__":
    test_registro_logs_crea_y_resume()
    print("OK test_4413_logs_proyecto")
