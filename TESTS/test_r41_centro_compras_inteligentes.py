from pathlib import Path

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI


def test_r41_proveedores_compras_y_persistencia(tmp_path: Path):
    core = HostAICore(tmp_path)

    prov = core.compras.crear_proveedor_manual(
        nombre="Frutas Norte",
        cif="B12345678",
        telefono="600111222",
        email="compras@frutasnorte.test",
    )
    assert prov.nombre == "Frutas Norte"
    assert prov.estado == "activo"

    core.compras.asociar_producto_proveedor(prov.id, "Tomate pera")
    core.compras.editar_proveedor(prov.id, observaciones="Entrega de lunes a viernes")

    compra = core.compras.registrar_compra_manual(
        producto="Tomate pera",
        cantidad=12,
        unidad="kg",
        proveedor="Frutas Norte",
        prioridad="Alta",
    )
    assert compra.origen_tipo == "manual"

    reiniciado = HostAICore(tmp_path)
    proveedores = reiniciado.compras.listar_proveedores(incluir_inactivos=True)
    assert any(p["nombre"] == "Frutas Norte" for p in proveedores)

    historial = reiniciado.compras.listar_historial_compras("Tomate")
    assert len(historial) == 1
    assert historial[0]["producto"] == "Tomate pera"


def test_r41_propuesta_inteligente_confirmar_y_cancelar(tmp_path: Path):
    core = HostAICore(tmp_path)

    core.produccion_real.listar_planes = lambda: [
        {
            "id": "PLAN-001",
            "nombre": "Plan Banquete",
            "estado": "planificado",
            "tareas": [
                {"receta_id": "REC-PAELLA", "cantidad": 10, "titulo": "Paella principal"},
            ],
        }
    ]

    core.escandallos_inteligente.calcular_necesidades_receta = lambda receta_id, raciones, origen="": {
        "necesidades": [
            {
                "nombre": "Arroz bomba",
                "unidad": "kg",
                "articulo_id": "ART-ARROZ",
                "cantidad_bruta": 8,
                "origen": origen,
                "proveedor_preferente": "Makro",
            }
        ]
    }

    core.stock.stock_actual = lambda: {
        "items": [
            {"nombre": "Arroz bomba", "unidad": "kg", "articulo_id": "ART-ARROZ", "cantidad": 2}
        ]
    }

    generadas = core.compras.generar_propuesta_compra_inteligente(core)
    assert generadas["total_propuestas"] == 1
    propuesta_id = generadas["propuestas"][0]["id"]

    compra = core.compras.confirmar_propuesta_compra(propuesta_id, proveedor="Makro")
    assert compra.origen_tipo == "inteligente"
    assert compra.cantidad == 6

    generadas_2 = core.compras.generar_propuesta_compra_inteligente(core)
    assert generadas_2["total_propuestas"] == 0
    assert len(core.compras.listar_propuestas_compra(solo_pendientes=True)) == 0


def test_r41_pipeline_acciones_basicas(tmp_path: Path):
    core = HostAICore(tmp_path)

    r_crear = core.orquestador.resolver(
        SolicitudHostAI(
            "crear_proveedor_manual",
            {
                "nombre": "Carnes Centro",
                "email": "info@carnescentro.test",
            },
        )
    )
    assert r_crear.ok is True
    proveedor_id = r_crear.datos["proveedor"]["id"]

    r_asociar = core.orquestador.resolver(
        SolicitudHostAI("asociar_producto_proveedor_compra", {"proveedor_id": proveedor_id, "producto": "Solomillo"})
    )
    assert r_asociar.ok is True

    r_compra = core.orquestador.resolver(
        SolicitudHostAI(
            "registrar_compra_manual",
            {"producto": "Solomillo", "cantidad": 5, "unidad": "kg", "proveedor": "Carnes Centro"},
        )
    )
    assert r_compra.ok is True

    r_historial = core.orquestador.resolver(SolicitudHostAI("listar_historial_compras", {"texto": "solomillo"}))
    assert r_historial.ok is True
    assert len(r_historial.datos["compras"]) == 1
