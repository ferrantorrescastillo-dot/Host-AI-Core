import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.instalador_host_ai_4415 import InstaladorHostAI4415


def main():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        instalador = InstaladorHostAI4415(base)

        estado_inicial = instalador.verificar_instalacion()
        assert estado_inicial["ok"] is False
        assert "APP" in estado_inicial["faltantes"]

        resultado = instalador.preparar_instalacion(restaurante="Restaurante Test")
        assert resultado["ok"] is True
        assert (base / "APP").exists()
        assert (base / "DATOS" / "configuracion" / "host_ai_config.json").exists()
        assert resultado["configuracion"]["restaurante"] == "Restaurante Test"

        estado_final = instalador.verificar_instalacion()
        assert estado_final["ok"] is True
        assert estado_final["faltantes"] == []

        informe = instalador.crear_informe_instalacion()
        assert informe["ok"] is True
        assert Path(informe["archivo"]).exists()

    print("TEST OK - Host AI 4.4.15 Instalador Host AI")


if __name__ == "__main__":
    main()
