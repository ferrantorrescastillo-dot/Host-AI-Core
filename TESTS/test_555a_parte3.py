from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from CORE.entidades.ingrediente import Ingrediente
from CORE.entidades.receta import Receta
from CORE.entidades.escandallo import Escandallo
from CORE.gestores.gestor_escandallos_555a import GestorEscandallos555A
from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        ruta_esc = base / "escandallos.json"
        ruta_stock = base / "stock.json"
        ruta_art = base / "articulos.json"

        arroz = Ingrediente(
            codigo="ING-ARROZ",
            articulo_id="ART-ARROZ",
            nombre="Arroz bomba",
            cantidad=1.0,
            unidad="kg",
            proveedor_habitual="Makro",
            precio_unitario=2.15,
        )
        caldo = Ingrediente(
            codigo="ING-CALDO",
            articulo_id="ART-CALDO",
            nombre="Caldo pescado",
            cantidad=3.0,
            unidad="L",
            proveedor_habitual="Proveedor caldo",
            precio_unitario=1.0,
        )
        receta = Receta(
            codigo="REC-PAELLA",
            nombre="Paella de marisco",
            rendimiento=10,
            unidad_rendimiento="personas",
            ingredientes=[arroz, caldo],
        )
        RepositorioEscandallos(ruta_esc).guardar_todos([Escandallo(receta=receta, coste_total=5.15)])

        ruta_stock.write_text(json.dumps([
            {"codigo": "ART-ARROZ", "articulo": "Arroz bomba", "unidad": "kg", "stock_actual": 10, "stock_minimo": 2, "proveedor": "Makro"},
            {"codigo": "ART-CALDO", "articulo": "Caldo pescado", "unidad": "L", "stock_actual": 20, "stock_minimo": 5, "proveedor": "Proveedor caldo"},
        ]), encoding="utf-8")
        ruta_art.write_text(json.dumps([
            {"codigo": "ART-ARROZ", "nombre": "Arroz bomba", "proveedor": "Makro", "precio": 2.15},
            {"codigo": "ART-CALDO", "nombre": "Caldo pescado", "proveedor": "Proveedor caldo", "precio": 1.0},
        ]), encoding="utf-8")

        gestor = GestorEscandallos555A(ruta_esc, ruta_stock, ruta_art)
        resultado = gestor.analizar_evento({"tipo": "boda", "personas": 150, "menu": "paella"})

        assert resultado["datos_reales_modificados"] is False
        assert resultado["produccion"]["factor"] == 15.0
        assert len(resultado["stock"]) == 2
        faltantes = {x["ingrediente"]: x["faltante"] for x in resultado["stock"]}
        assert faltantes["Arroz bomba"] == 5.0
        assert faltantes["Caldo pescado"] == 25.0
        assert len(resultado["compras_propuestas"]) == 2
        assert len(resultado["incidencias"]) == 2

    print("TEST OK 5.5.5A PARTE 3 - Integración stock, compras, producción y eventos")


if __name__ == "__main__":
    main()
