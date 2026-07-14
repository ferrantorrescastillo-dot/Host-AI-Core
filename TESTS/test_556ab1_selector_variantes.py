from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.conector_produccion_real_556 import procesar_consulta_produccion_real_556


def _ficha(codigo: str, hoja: str, fila: int, nombre: str, ingredientes: list[dict]) -> dict:
    return {
        "codigo": codigo, "nombre": nombre, "estado": "REVISAR", "accion": "OMITIR",
        "hoja": hoja, "fila_inicio": fila, "rendimiento": 1, "unidad_rendimiento": "pax",
        "ingredientes": ingredientes,
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "DATOS/db").mkdir(parents=True)
        (root / "DATOS/informes").mkdir(parents=True)
        (root / "DATOS/db/escandallos_canonicos.json").write_text('{"escandallos": []}', encoding="utf-8")
        (root / "DATOS/db/articulos.json").write_text('[]', encoding="utf-8")
        fichas = [
            _ficha("R1", "M.P Aperitivos", 4, "Patatas Bravas", [{"nombre":"Patata", "cantidad":0.35, "unidad":"kg"}]),
            _ficha("R2", "M.P MENU BBQ.", 25, "Patatas bravas", [{"nombre":"Patata", "cantidad":0.1, "unidad":"kg"}]),
        ]
        (root / "DATOS/informes/preimportacion_555b.json").write_text(json.dumps({"fichas": fichas}), encoding="utf-8")
        resolucion = {"decisiones": [{
            "nombre": "Patatas Bravas", "tipo": "VARIANTES_REALES",
            "fichas_origen": ["M.P Aperitivos:4", "M.P MENU BBQ.:25"],
            "nombres_propuestos": ["Patatas Bravas — Aperitivos", "Patatas Bravas — BBQ"],
        }]}
        (root / "DATOS/informes/resolucion_variantes_555b.json").write_text(json.dumps(resolucion), encoding="utf-8")

        primera = procesar_consulta_produccion_real_556("Desglosa la producción de Patatas bravas para 100 personas", root)
        assert primera["estado"] == "seleccion_requerida"
        assert len(primera["datos"]["opciones"]) == 2
        segunda = procesar_consulta_produccion_real_556("2", root)
        assert segunda["ok"] is True
        assert segunda["datos"]["receta"] == "Patatas Bravas — BBQ"
        assert segunda["datos"]["datos_reales_modificados"] is False
    print("TEST OK 5.5.6AB.1 - Selector conversacional de variantes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
