import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.configuracion_central_4414 import GestorConfiguracionCentral4414


def main():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        gestor = GestorConfiguracionCentral4414(base)

        config = gestor.crear_si_no_existe()
        assert config["restaurante"] == "Restaurante Demo"
        assert gestor.config_path.exists()

        actualizada = gestor.actualizar_configuracion({
            "restaurante": "Boronat",
            "iva_default": 21,
            "ocr_activo": True,
            "ia_activa": True,
        })
        assert actualizada["restaurante"] == "Boronat"
        assert actualizada["iva_default"] == 21.0
        assert actualizada["ocr_activo"] is True

        validacion = gestor.validar_configuracion()
        assert validacion["ok"] is True
        assert validacion["errores"] == []

        rutas = gestor.asegurar_rutas_configuradas()
        assert rutas["ok"] is True
        assert (base / "DATOS").exists()
        assert (base / "Documentos").exists()
        assert (base / "LOGS").exists()

        resumen = gestor.resumen_configuracion()
        assert resumen["restaurante"] == "Boronat"
        assert resumen["ok"] is True

    print("TEST OK - Host AI 4.4.14 Configuración Central")


if __name__ == "__main__":
    main()
