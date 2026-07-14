from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from CORE.entidades.escandallo import Escandallo
from CORE.entidades.ingrediente import Ingrediente
from CORE.entidades.receta import Receta
from CORE.gestores.gestor_escandallos_555a import GestorEscandallos555A
from SERVICIOS.auditor_modelo_escandallos_555a import auditar_modelo_555a
from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos
from SERVICIOS.serializador_escandallos_555a import escandallo_a_dict, escandallo_desde_dict


def _crear_escandallo() -> Escandallo:
    receta = Receta(
        codigo="REC-PAELLA-001",
        nombre="Paella de marisco",
        rendimiento=10,
        unidad_rendimiento="personas",
        ingredientes=[
            Ingrediente(
                codigo="ART-ARROZ",
                articulo_id="ART-ARROZ",
                nombre="Arroz bomba",
                cantidad=1.0,
                unidad="kg",
                precio_unitario=2.15,
                proveedor_habitual="Makro",
            ),
            Ingrediente(
                codigo="ART-CALDO",
                articulo_id="ART-CALDO",
                nombre="Caldo de pescado",
                cantidad=5.0,
                unidad="l",
                precio_unitario=1.2,
                proveedor_habitual="Proveedor caldo",
            ),
        ],
    )
    return Escandallo(receta=receta, coste_total=8.15)


def main() -> None:
    with tempfile.TemporaryDirectory() as temporal:
        base = Path(temporal)
        ruta_repo = base / "escandallos_canonicos.json"
        ruta_stock = base / "stock_inicial.json"
        ruta_articulos = base / "articulos.json"

        ruta_stock.write_text(
            json.dumps(
                [
                    {"codigo": "ART-ARROZ", "articulo": "Arroz bomba", "stock_actual": 8, "stock_minimo": 2, "unidad": "kg", "proveedor": "Makro"},
                    {"codigo": "ART-CALDO", "articulo": "Caldo de pescado", "stock_actual": 20, "stock_minimo": 5, "unidad": "l", "proveedor": "Proveedor caldo"},
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        ruta_articulos.write_text(
            json.dumps(
                [
                    {"codigo": "ART-ARROZ", "nombre": "Arroz bomba", "precio": 2.15, "proveedor": "Makro"},
                    {"codigo": "ART-CALDO", "nombre": "Caldo de pescado", "precio": 1.2, "proveedor": "Proveedor caldo"},
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        hash_stock_antes = ruta_stock.read_bytes()
        hash_articulos_antes = ruta_articulos.read_bytes()

        escandallo = _crear_escandallo()
        payload = escandallo_a_dict(escandallo)
        restaurado = escandallo_desde_dict(payload)
        assert restaurado.receta.nombre == "Paella de marisco"
        assert len(restaurado.receta.ingredientes) == 2

        repo = RepositorioEscandallos(ruta_repo)
        assert repo.upsert(restaurado) == "creado"
        assert repo.upsert(restaurado) == "actualizado"
        assert len(repo.listar()) == 1
        assert len(repo.buscar_por_nombre("paella")) == 1
        assert len(repo.buscar_por_ingrediente("arroz")) == 1

        gestor = GestorEscandallos555A(ruta_repo, ruta_stock, ruta_articulos)
        resultado = gestor.analizar_evento({"tipo": "boda", "personas": 100, "menu": "paella"})
        assert resultado["escandallo"] == "Paella de marisco"
        assert resultado["produccion"]["factor"] == 10.0
        assert resultado["datos_reales_modificados"] is False
        assert any(linea["ingrediente"] == "Arroz bomba" for linea in resultado["stock"])
        assert resultado["compras_propuestas"], "Debe proponer compra cuando hay faltantes"

        assert ruta_stock.read_bytes() == hash_stock_antes
        assert ruta_articulos.read_bytes() == hash_articulos_antes

        informe = auditar_modelo_555a(repo)
        assert informe.estado == "MODELO_CANONICO_APROBADO"
        assert informe.aprobadas == informe.total

    print("TEST OK 5.5.5A PARTE 4 - Cierre, serialización y regresión completa")


if __name__ == "__main__":
    main()
