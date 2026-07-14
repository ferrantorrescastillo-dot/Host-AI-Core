from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.conector_escandallos_real_555 import (
    ConectorEscandallosReal555,
    extraer_termino_escandallo_555,
    procesar_consulta_escandallos_real_555,
)


def escribir(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
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
                                {"nombre": "Patata Monalisa", "cantidad": 0.3, "unidad": "kg"},
                                {"nombre": "Gamba paella", "cantidad": 0.19, "unidad": "kg"},
                            ],
                        },
                        "coste_total": 2.5,
                    }
                ],
            },
        )
        escribir(root / "DATOS/db/escandallos.json", [])

        conector = ConectorEscandallosReal555(root)
        por_ingrediente = conector.consultar("patata monalisa")
        assert por_ingrediente["encontrado"] is True
        assert por_ingrediente["coincidencias"][0]["nombre"] == "Ensaladilla de gamba"
        assert "escandallos_canonicos.json" in por_ingrediente["fuente"]

        assert extraer_termino_escandallo_555("Busca una receta que contenga ensaladilla.") == "ensaladilla"
        por_nombre = procesar_consulta_escandallos_real_555(
            "Busca una receta que contenga ensaladilla.", root
        )
        assert por_nombre["gestionado"] is True
        assert "Ensaladilla de gamba" in por_nombre["mensaje"]
        assert "escandallos_canonicos.json" in por_nombre["mensaje"]

    print("TEST OK 5.5.5B.7.2.1 - Búsquedas canónicas por ingrediente y nombre")


if __name__ == "__main__":
    main()
