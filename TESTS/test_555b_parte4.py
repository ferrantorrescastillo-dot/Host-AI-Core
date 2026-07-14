from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from SERVICIOS.depurador_fichas_tecnicas_555b import DepuradorFichasTecnicas555B


def _ficha(nombre, ingredientes, rendimiento=1, unidad="u", hoja="M.P TEST", fila=4):
    return {
        "hoja": hoja,
        "fila_inicio": fila,
        "fila_fin": fila + 10,
        "nombre": nombre,
        "rendimiento": rendimiento,
        "unidad_rendimiento": unidad,
        "confianza": 95.0,
        "ingredientes": [
            {"nombre": n, "cantidad": c, "unidad": u, "fila_origen": fila + i + 1}
            for i, (n, c, u) in enumerate(ingredientes)
        ],
    }


def main() -> None:
    origen = {
        "archivo": "prueba.xlsx",
        "fichas": [
            _ficha("Salsa romesco", [("Tomate", 1, "kg")], rendimiento=1, unidad="kg", fila=4),
            _ficha("Plato con romesco", [("Salsa romesco", 0.1, "kg"), ("Huevos L", 2, "kg")], fila=20),
            _ficha("Salsa romesco", [("Tomate", 1, "kg")], rendimiento=1, unidad="kg", fila=40),
            _ficha("KG", [("Pan", 0.1, "kg")], fila=60),
        ],
        "errores": [],
    }
    resultado = DepuradorFichasTecnicas555B().depurar_resultado(origen)
    assert resultado["resumen"]["fichas_analizadas"] == 4
    assert resultado["resumen"]["grupos_duplicados"] == 1
    assert resultado["resumen"]["a_revisar"] >= 1
    plato = next(f for f in resultado["fichas"] if f["nombre_original"] == "Plato con romesco")
    assert "Salsa romesco" in plato["elaboraciones_referenciadas"]
    huevo = next(i for i in plato["ingredientes"] if i["nombre"] == "Huevos L")
    assert huevo["unidad_normalizada"] == "u"
    invalida = next(f for f in resultado["fichas"] if f["nombre_original"] == "KG")
    assert invalida["estado"] == "REVISAR"
    assert resultado["datos_reales_modificados"] is False
    assert resultado["escandallos_importados"] == 0
    print("TEST OK 5.5.5B PARTE 4 - Depuración, duplicados, unidades y elaboraciones")


if __name__ == "__main__":
    main()
