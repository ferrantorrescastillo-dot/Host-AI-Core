import sys
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.gestor_multi_restaurante_452 import GestorMultiRestaurante452


def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        gestor = GestorMultiRestaurante452(base)
        creado = gestor.crear_restaurante("Boronat Restaurant", "restaurante")
        assert creado["ok"] is True
        assert creado["restaurante"]["slug"] == "boronat_restaurant"
        assert (base / "Restaurantes" / "boronat_restaurant" / "DATOS" / "db").exists()

        creado2 = gestor.crear_restaurante("Catering Ferran", "catering")
        assert creado2["ok"] is True
        listado = gestor.listar_restaurantes()
        assert listado["total"] == 2

        seleccionado = gestor.seleccionar_restaurante("Boronat Restaurant")
        assert seleccionado["ok"] is True
        activo = gestor.obtener_restaurante_activo()
        assert activo["ok"] is True
        assert activo["restaurante"]["slug"] == "boronat_restaurant"
        ruta = gestor.ruta_restaurante_activo()
        assert ruta["ok"] is True
        assert ruta["ruta"].endswith("boronat_restaurant")

    print("TEST OK - Host AI 4.5.2 Multi Restaurante")


if __name__ == "__main__":
    main()
