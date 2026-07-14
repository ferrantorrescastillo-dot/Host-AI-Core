from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from SERVICIOS.resolutor_variantes_escandallos_555b import ResolutorInteligenteEscandallos555B


def _ficha(codigo: str, nombre: str, hoja: str, ingredientes, rendimiento=4.0, estado="PREPARADA"):
    return {
        "codigo": codigo,
        "nombre": nombre,
        "estado": estado,
        "accion": "OMITIR" if estado == "REVISAR" else "CREAR",
        "motivo": "prueba",
        "hoja": hoja,
        "fila_inicio": 4,
        "fila_fin": 20,
        "rendimiento": rendimiento,
        "unidad_rendimiento": "u",
        "ingredientes": [
            {"nombre": n, "cantidad": c, "unidad": u} for n, c, u in ingredientes
        ],
        "relaciones_articulos": [
            {"ingrediente": n, "estado": "ENLAZADO"} for n, _, _ in ingredientes
        ],
        "confianza": 95.0,
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        informe = base / "pre.json"
        contenido = {
            "archivo_excel": "prueba.xlsx",
            "fichas": [
                _ficha("A1", "Salsa romesco", "M.P A", [("Tomate", 1, "kg"), ("Ajo", 0.1, "kg")]),
                _ficha("A2", "Salsa romesco", "M.P B", [("Tomate", 1, "kg"), ("Ajo", 0.1, "kg")]),
                _ficha("B1", "Patatas bravas", "M.P C", [("Patata", 1, "kg"), ("Salsa", 0.2, "kg")]),
                _ficha("B2", "Patatas bravas", "M.P D", [("Patata", 1, "kg"), ("Salsa", 0.25, "kg")]),
                _ficha("C1", "Botifarra", "M.P E", [("Botifarra", 1, "u")]),
                _ficha("C2", "Botifarra", "M.P F", [("Mongeta", 0.2, "kg"), ("Botifarra", 1, "u")]),
                _ficha("X1", "KG", "M.P X", [("Pan", 1, "kg")], estado="REVISAR"),
            ],
        }
        informe.write_text(json.dumps(contenido, ensure_ascii=False), encoding="utf-8")
        servicio = ResolutorInteligenteEscandallos555B(base / "articulos.json", base / "destino.json")
        resultado = servicio.ejecutar("prueba.xlsx", informe_preimportacion=informe)

        assert resultado["datos_reales_modificados"] is False
        assert resultado["resumen"]["grupos_analizados"] == 3
        assert resultado["resumen"]["seleccionar_una"] >= 1
        assert resultado["resumen"]["fusionar_duplicados"] >= 1
        assert resultado["resumen"]["mantener_variantes"] >= 1
        assert resultado["resumen"]["revisar_titulo"] == 1
        assert not (base / "destino.json").exists()

    print("TEST OK 5.5.5B PARTE 6 - Resolución inteligente de duplicados y variantes")


if __name__ == "__main__":
    main()
