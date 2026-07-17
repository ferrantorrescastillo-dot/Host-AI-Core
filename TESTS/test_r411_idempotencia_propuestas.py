from pathlib import Path

from CORE.host_ai_core import HostAICore


def _mock_contexto(core, necesidad=8.0, stock=2.0, origen="Plan / Receta", producto="Arroz bomba", unidad="kg", articulo_id="ART-ARROZ"):
    core.produccion_real.listar_planes = lambda: [
        {
            "id": "PLAN-001",
            "nombre": "Plan Banquete",
            "estado": "planificado",
            "tareas": [{"receta_id": "REC-PAELLA", "cantidad": 10, "titulo": "Paella"}],
        }
    ]

    core.escandallos_inteligente.calcular_necesidades_receta = lambda receta_id, raciones, origen="": {
        "necesidades": [
            {
                "nombre": producto,
                "unidad": unidad,
                "articulo_id": articulo_id,
                "cantidad_bruta": necesidad,
                "origen": origen or "Plan / Receta",
                "proveedor_preferente": "Makro",
            }
        ]
    }

    core.stock.stock_actual = lambda: {
        "items": [{"nombre": producto, "unidad": unidad, "articulo_id": articulo_id, "cantidad": stock}]
    }


def test_r411_caso_1_generacion_repetida_no_duplica(tmp_path: Path):
    core = HostAICore(tmp_path)
    _mock_contexto(core, necesidad=8.0, stock=2.0)

    r1 = core.compras.generar_propuesta_compra_inteligente(core)
    assert r1["resumen"]["propuestas_nuevas"] == 1

    r2 = core.compras.generar_propuesta_compra_inteligente(core)
    pendientes = core.compras.listar_propuestas_compra(solo_pendientes=True)
    assert len(pendientes) == 1
    assert r2["resumen"]["propuestas_nuevas"] == 0
    assert r2["resumen"]["propuestas_actualizadas"] == 0


def test_r411_caso_2_compra_confirmada_no_repropone(tmp_path: Path):
    core = HostAICore(tmp_path)
    _mock_contexto(core, necesidad=8.0, stock=2.0)

    generado = core.compras.generar_propuesta_compra_inteligente(core)
    pid = generado["propuestas"][0]["id"]
    compra = core.compras.confirmar_propuesta_compra(pid, proveedor="Makro")
    assert compra.cantidad == 6

    nuevo = core.compras.generar_propuesta_compra_inteligente(core)
    assert nuevo["resumen"]["propuestas_nuevas"] == 0
    assert len(core.compras.listar_propuestas_compra(solo_pendientes=True)) == 0


def test_r411_caso_3_cobertura_parcial_compra_existente(tmp_path: Path):
    core = HostAICore(tmp_path)
    _mock_contexto(core, necesidad=10.0, stock=2.0)

    core.compras.registrar_compra_manual(
        producto="Arroz bomba",
        cantidad=5,
        unidad="kg",
        proveedor="Makro",
        articulo_id="ART-ARROZ",
    )

    generado = core.compras.generar_propuesta_compra_inteligente(core)
    propuesta = generado["propuestas"][0]
    assert propuesta["comprar"] == 3


def test_r411_caso_4_cancelada_puede_regenerarse(tmp_path: Path):
    core = HostAICore(tmp_path)
    _mock_contexto(core, necesidad=8.0, stock=2.0)

    generado = core.compras.generar_propuesta_compra_inteligente(core)
    pid = generado["propuestas"][0]["id"]
    core.compras.cancelar_propuesta_compra(pid)

    nuevo = core.compras.generar_propuesta_compra_inteligente(core)
    pendientes = core.compras.listar_propuestas_compra(solo_pendientes=True)
    assert len(pendientes) == 1
    assert pendientes[0]["id"] != pid
    assert nuevo["resumen"]["propuestas_nuevas"] == 1


def test_r411_caso_5_y_6_cambio_necesidad_actualiza_sin_duplicar(tmp_path: Path):
    core = HostAICore(tmp_path)
    _mock_contexto(core, necesidad=8.0, stock=2.0)

    core.compras.generar_propuesta_compra_inteligente(core)
    pendientes = core.compras.listar_propuestas_compra(solo_pendientes=True)
    assert len(pendientes) == 1
    pid = pendientes[0]["id"]
    assert pendientes[0]["comprar"] == 6

    _mock_contexto(core, necesidad=10.0, stock=2.0)
    core.compras.generar_propuesta_compra_inteligente(core)
    pendientes = core.compras.listar_propuestas_compra(solo_pendientes=True)
    assert len(pendientes) == 1
    assert pendientes[0]["id"] == pid
    assert pendientes[0]["comprar"] == 8

    _mock_contexto(core, necesidad=7.0, stock=2.0)
    core.compras.generar_propuesta_compra_inteligente(core)
    pendientes = core.compras.listar_propuestas_compra(solo_pendientes=True)
    assert len(pendientes) == 1
    assert pendientes[0]["id"] == pid
    assert pendientes[0]["comprar"] == 5


def test_r411_caso_7_necesidad_completamente_cubierta(tmp_path: Path):
    core = HostAICore(tmp_path)
    _mock_contexto(core, necesidad=8.0, stock=1.0)

    core.compras.generar_propuesta_compra_inteligente(core)
    assert len(core.compras.listar_propuestas_compra(solo_pendientes=True)) == 1

    _mock_contexto(core, necesidad=8.0, stock=8.0)
    core.compras.generar_propuesta_compra_inteligente(core)
    assert len(core.compras.listar_propuestas_compra(solo_pendientes=True)) == 0


def test_r411_caso_8_duplicados_preexistentes_se_consolidan(tmp_path: Path):
    core = HostAICore(tmp_path)
    _mock_contexto(core, necesidad=8.0, stock=2.0)

    r1 = core.compras.generar_propuesta_compra_inteligente(core)
    base = r1["propuestas"][0]

    dup = dict(base)
    dup["id"] = "PROP-DUPLICADA"
    dup["estado"] = "pendiente"
    dup["creado_en"] = "9999-12-31T23:59:59"
    dup["actualizado_en"] = dup["creado_en"]
    from MODELOS.compras import PropuestaCompraInteligente

    core.compras.propuestas_compra[dup["id"]] = PropuestaCompraInteligente.from_dict(dup)
    core.compras._guardar()

    core.compras.generar_propuesta_compra_inteligente(core)
    pendientes = core.compras.listar_propuestas_compra(solo_pendientes=True)
    assert len(pendientes) == 1
    assert pendientes[0]["comprar"] == 6


def test_r411_caso_9_origenes_distinto_orden_misma_necesidad(tmp_path: Path):
    core = HostAICore(tmp_path)

    core.produccion_real.listar_planes = lambda: [
        {
            "id": "PLAN-001",
            "nombre": "Plan",
            "estado": "planificado",
            "tareas": [{"receta_id": "REC-1", "cantidad": 1, "titulo": "A"}],
        }
    ]

    def calc(_rid, _raciones, origen=""):
        return {
            "necesidades": [
                {
                    "nombre": "Tomate",
                    "unidad": "kg",
                    "articulo_id": "ART-TOMATE",
                    "cantidad_bruta": 4,
                    "origen": "Zeta",
                    "proveedor_preferente": "Sarda",
                },
                {
                    "nombre": "Tomate",
                    "unidad": "kg",
                    "articulo_id": "ART-TOMATE",
                    "cantidad_bruta": 2,
                    "origen": "Alfa",
                    "proveedor_preferente": "Sarda",
                },
            ]
        }

    core.escandallos_inteligente.calcular_necesidades_receta = calc
    core.stock.stock_actual = lambda: {"items": [{"nombre": "Tomate", "unidad": "kg", "articulo_id": "ART-TOMATE", "cantidad": 0}]}

    core.compras.generar_propuesta_compra_inteligente(core)

    def calc_orden_inverso(_rid, _raciones, origen=""):
        return {
            "necesidades": [
                {
                    "nombre": "Tomate",
                    "unidad": "kg",
                    "articulo_id": "ART-TOMATE",
                    "cantidad_bruta": 2,
                    "origen": "Alfa",
                    "proveedor_preferente": "Sarda",
                },
                {
                    "nombre": "Tomate",
                    "unidad": "kg",
                    "articulo_id": "ART-TOMATE",
                    "cantidad_bruta": 4,
                    "origen": "Zeta",
                    "proveedor_preferente": "Sarda",
                },
            ]
        }

    core.escandallos_inteligente.calcular_necesidades_receta = calc_orden_inverso
    core.compras.generar_propuesta_compra_inteligente(core)

    pendientes = core.compras.listar_propuestas_compra(solo_pendientes=True)
    assert len(pendientes) == 1
    assert pendientes[0]["comprar"] == 6
