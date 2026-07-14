from pathlib import Path
from types import SimpleNamespace

from SERVICIOS.contexto_global_rr161a import ContextoGlobalRR161A
from APP.consola import AppConsolaHostAI


def test_contexto_persiste_evento_plan_pedido_y_receta(tmp_path):
    c1 = ContextoGlobalRR161A(tmp_path)
    c1.establecer("evento_id", "EVT-RR1")
    c1.establecer("plan_produccion_id", "PLAN-RR1")
    c1.establecer("pedido_compra_id", "PED-RR1")
    c1.establecer("escandallo_id", "REC-RR1")

    c2 = ContextoGlobalRR161A(tmp_path)
    assert c2.obtener("evento_id") == "EVT-RR1"
    assert c2.obtener("plan_produccion_id") == "PLAN-RR1"
    assert c2.obtener("pedido_compra_id") == "PED-RR1"
    assert c2.obtener("escandallo_id") == "REC-RR1"


def test_asignaciones_consola_actualizan_contexto_persistente(tmp_path):
    core = SimpleNamespace(base_dir=tmp_path)
    app = AppConsolaHostAI(core)
    app.ultimo_evento_id = "EVT-278D20DD"
    app.ultimo_plan_produccion_id = "PLANPR-BE545287E9"

    reiniciada = AppConsolaHostAI(core)
    assert reiniciada.ultimo_evento_id == "EVT-278D20DD"
    assert reiniciada.ultimo_plan_produccion_id == "PLANPR-BE545287E9"


def test_limpiar_evento_no_borra_otros_contextos(tmp_path):
    contexto = ContextoGlobalRR161A(tmp_path)
    contexto.establecer("evento_id", "EVT-1")
    contexto.establecer("pedido_compra_id", "PED-1")
    contexto.establecer("evento_id", None)

    assert contexto.obtener("evento_id") is None
    assert contexto.obtener("pedido_compra_id") == "PED-1"


def test_contador_precios_incluye_registrados_y_escandallos(tmp_path):
    costes = SimpleNamespace(listar_precios=lambda: {
        "total": 1,
        "precios": [{"articulo_id": "ART-1", "nombre": "Arroz", "precio_unitario": 1.65}],
    })
    escandallos = SimpleNamespace(listar=lambda incluir: [{
        "lineas": [
            {"articulo_id": "ART-1", "nombre": "Arroz", "coste_unitario": 1.65},
            {"articulo_id": "ART-2", "nombre": "Carrillera", "coste_unitario": 8.5},
            {"elaboracion_id": "ELAB-1", "nombre": "Demi-glace", "coste_unitario": 3.0},
        ]
    }])
    core = SimpleNamespace(base_dir=tmp_path, costes_inteligente=costes, escandallos_inteligente=escandallos)
    app = AppConsolaHostAI(core)

    assert app._total_precios_disponibles() == 3
