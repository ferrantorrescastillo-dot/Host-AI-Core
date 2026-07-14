from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Permite ejecutar el test directamente con:
# python TESTS/test_555b72_conector_modelo_canonico.py
RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from SERVICIOS.buscador_catalogo_cocina_552 import (  # noqa: E402
    BuscadorCatalogoCocina552,
    formatear_resultado_552,
)
from SERVICIOS.lector_modelo_canonico_555b72 import LectorModeloCanonico555B72  # noqa: E402


def escribir(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        escribir(root / "DATOS/db/escandallos.json", {"escandallos": [{"nombre": "LEGACY NO DEBE GANAR"}]})
        escribir(
            root / "DATOS/db/escandallos_canonicos.json",
            {
                "schema_version": "1.0",
                "escandallos": [
                    {
                        "receta": {
                            "codigo": "REC-001",
                            "nombre": "Ensaladilla de gamba",
                            "rendimiento": 4,
                            "unidad_rendimiento": "u",
                            "ingredientes": [
                                {
                                    "codigo": "ING-1",
                                    "nombre": "Patata Monalisa",
                                    "cantidad": 0.3,
                                    "unidad": "kg",
                                }
                            ],
                        },
                        "coste_total": 2.5,
                    }
                ],
            },
        )
        escribir(root / "DATOS/db/articulos.json", {"articulos": []})
        escribir(root / "DATOS/db/proveedores.json", {"proveedores": []})

        lector = LectorModeloCanonico555B72(root).cargar()
        assert lector["modelo"] == "CANONICO_5.5.5A"
        assert len(lector["escandallos"]) == 1
        assert lector["escandallos"][0]["nombre"] == "Ensaladilla de gamba"

        buscador = BuscadorCatalogoCocina552(root)
        listado = buscador.listar("recetas")
        assert listado["total"] == 1
        assert listado["resultados"] == ["Ensaladilla de gamba"]
        assert "escandallos_canonicos.json" in listado["fuente"]

        busqueda = buscador.buscar("patata monalisa")
        assert busqueda["grupos"][0]["total"] == 1
        assert busqueda["grupos"][0]["resultados"][0]["nombre"] == "Ensaladilla de gamba"
        texto = formatear_resultado_552(listado)
        assert "Total: 1" in texto
        assert "escandallos_canonicos.json" in texto

    print("TEST OK 5.5.5B.7.2 - Conector del asistente al modelo canónico")


if __name__ == "__main__":
    main()
