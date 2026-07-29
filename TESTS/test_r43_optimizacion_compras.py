from datetime import datetime, timedelta
from pathlib import Path

import pytest

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI
from MODELOS.compras import PropuestaCompraInteligente


def _crear_proveedor(core, nombre):
    return core.compras.crear_proveedor_manual(nombre=nombre)


def _asociar(core, producto, proveedor_id, **kwargs):
    return core.compras.asociar_producto_proveedor_detallado(producto, proveedor_id, **kwargs)


def _crear_propuesta(core, producto="Tomate", cantidad=5.0, unidad="kg", prioridad="Alta"):
    p = PropuestaCompraInteligente(
        producto=producto,
        necesario=cantidad,
        disponible=0,
        comprar=cantidad,
        unidad=unidad,
        origen="Plan X",
        prioridad=prioridad,
        estado="pendiente",
    )
    core.compras.propuestas_compra[p.id] = p
    core.compras._guardar()
    return p


def test_r43_caso_01_descarta_proveedor_inactivo(tmp_path: Path):
    core = HostAICore(tmp_path)
    a = _crear_proveedor(core, "Activo")
    b = _crear_proveedor(core, "Inactivo")
    _asociar(core, "Tomate", a.id, precio_habitual=2.0, unidad_precio="kg")
    _asociar(core, "Tomate", b.id, precio_habitual=1.0, unidad_precio="kg")
    core.compras.desactivar_proveedor(b.id)

    r = core.compras.evaluar_proveedores_producto("Tomate", 2, "kg")
    assert len(r) == 1
    assert r[0]["proveedor_nombre"] == "Activo"


def test_r43_caso_02_descarta_asociacion_inactiva(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "P1")
    aso = _asociar(core, "Tomate", p.id, precio_habitual=2.0, unidad_precio="kg")
    core.compras.desactivar_asociacion_producto_proveedor(aso.id)

    r = core.compras.evaluar_proveedores_producto("Tomate", 2, "kg")
    assert r == []


def test_r43_caso_03_preferente_puntua_positivo(tmp_path: Path):
    core = HostAICore(tmp_path)
    a = _crear_proveedor(core, "A")
    b = _crear_proveedor(core, "B")
    _asociar(core, "Tomate", a.id, precio_habitual=3.0, unidad_precio="kg", preferente=True)
    _asociar(core, "Tomate", b.id, precio_habitual=2.0, unidad_precio="kg")

    r = core.compras.evaluar_proveedores_producto("Tomate", 1, "kg")
    assert any(x["proveedor_nombre"] == "A" and x["preferente"] for x in r)


def test_r43_caso_04_preferente_puede_perder_por_plazo_grave(tmp_path: Path):
    core = HostAICore(tmp_path)
    a = _crear_proveedor(core, "Preferente")
    b = _crear_proveedor(core, "Rapido")
    _asociar(core, "Tomate", a.id, precio_habitual=1.0, unidad_precio="kg", preferente=True, plazo_entrega_dias=8)
    _asociar(core, "Tomate", b.id, precio_habitual=1.3, unidad_precio="kg", plazo_entrega_dias=1)

    fecha_necesaria = (datetime.now() + timedelta(days=2)).date().isoformat()
    r = core.compras.evaluar_proveedores_producto("Tomate", 1, "kg", fecha_necesaria=fecha_necesaria)
    assert r[0]["proveedor_nombre"] == "Rapido"


def test_r43_caso_05_precio_desconocido_no_equivale_a_cero(tmp_path: Path):
    core = HostAICore(tmp_path)
    a = _crear_proveedor(core, "SinPrecio")
    b = _crear_proveedor(core, "ConPrecio")
    _asociar(core, "Tomate", a.id)
    _asociar(core, "Tomate", b.id, precio_habitual=3.0, unidad_precio="kg")

    r = core.compras.evaluar_proveedores_producto("Tomate", 1, "kg")
    sin_precio = next(x for x in r if x["proveedor_nombre"] == "SinPrecio")
    assert sin_precio["coste_total_estimado"] is None


def test_r43_caso_06_precio_cero_es_valido(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "Promo")
    _asociar(core, "Tomate", p.id, precio_habitual=0.0, unidad_precio="kg")

    r = core.compras.evaluar_proveedores_producto("Tomate", 2, "kg")
    assert r[0]["coste_total_estimado"] == 0.0


def test_r43_caso_07_unidad_incompatible_no_inventa_coste(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "Caja")
    _asociar(core, "Tomate", p.id, precio_habitual=10.0, unidad_precio="caja")

    r = core.compras.evaluar_proveedores_producto("Tomate", 2, "kg")
    assert r[0]["coste_total_estimado"] is None


def test_r43_caso_08_pedido_minimo_no_alcanzado(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "Mayorista")
    core.compras.editar_condiciones_proveedor(p.id, pedido_minimo_importe=100)
    _asociar(core, "Tomate", p.id, precio_habitual=5.0, unidad_precio="kg")

    r = core.compras.evaluar_proveedores_producto("Tomate", 5, "kg")
    assert r[0]["cumple_pedido_minimo"] is False
    assert r[0]["faltante_pedido_minimo"] > 0


def test_r43_caso_09_pedido_minimo_alcanzado(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "Mayorista")
    core.compras.editar_condiciones_proveedor(p.id, pedido_minimo_importe=20)
    _asociar(core, "Tomate", p.id, precio_habitual=5.0, unidad_precio="kg")

    r = core.compras.evaluar_proveedores_producto("Tomate", 5, "kg")
    assert r[0]["cumple_pedido_minimo"] is True


def test_r43_caso_10_portes_gratis_desde_umbral(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "Portes")
    core.compras.editar_condiciones_proveedor(p.id, portes=9, portes_gratis_desde=30)
    _asociar(core, "Tomate", p.id, precio_habitual=10.0, unidad_precio="kg")

    r = core.compras.evaluar_proveedores_producto("Tomate", 3, "kg")
    assert r[0]["portes_estimados"] == 0.0


def test_r43_caso_11_portes_aplicados_sin_umbral(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "Portes")
    core.compras.editar_condiciones_proveedor(p.id, portes=9, portes_gratis_desde=30)
    _asociar(core, "Tomate", p.id, precio_habitual=5.0, unidad_precio="kg")

    r = core.compras.evaluar_proveedores_producto("Tomate", 2, "kg")
    assert r[0]["portes_estimados"] == 9.0


def test_r43_caso_12_cantidad_minima_producto(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "Minimo")
    _asociar(core, "Tomate", p.id, precio_habitual=4.0, unidad_precio="kg", cantidad_minima_producto=10)

    r = core.compras.evaluar_proveedores_producto("Tomate", 2, "kg")
    assert r[0]["cumple_cantidad_minima_producto"] is False


def test_r43_caso_13_fallback_proveedor_sugerido_sin_asociaciones(tmp_path: Path):
    core = HostAICore(tmp_path)
    _crear_proveedor(core, "Sugerido")

    r = core.compras.evaluar_proveedores_producto("Producto X", 1, "u", proveedor_sugerido="Sugerido")
    assert len(r) == 1
    assert r[0]["proveedor_nombre"] == "Sugerido"


def test_r43_caso_14_recomendacion_propuesta_sin_side_effects(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "A")
    _asociar(core, "Tomate", p.id, precio_habitual=2.0, unidad_precio="kg")
    propuesta = _crear_propuesta(core, "Tomate", 2, "kg")

    antes = core.compras.propuestas_compra[propuesta.id].to_dict()
    core.compras.recomendar_proveedor_para_propuesta(propuesta.id)
    despues = core.compras.propuestas_compra[propuesta.id].to_dict()
    assert antes == despues


def test_r43_caso_15_listar_propuestas_es_consulta_pura(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "A")
    _asociar(core, "Tomate", p.id, precio_habitual=2.0, unidad_precio="kg")
    propuesta = _crear_propuesta(core, "Tomate", 2, "kg")

    antes = core.compras.propuestas_compra[propuesta.id].to_dict()
    core.compras.listar_propuestas_compra(solo_pendientes=True)
    despues = core.compras.propuestas_compra[propuesta.id].to_dict()
    assert antes == despues


def test_r43_caso_16_agrupacion_es_consulta_pura(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "A")
    _asociar(core, "Tomate", p.id, precio_habitual=2.0, unidad_precio="kg")
    propuesta = _crear_propuesta(core, "Tomate", 2, "kg")

    antes = core.compras.propuestas_compra[propuesta.id].to_dict()
    core.compras.agrupar_propuestas_por_proveedor_recomendado()
    despues = core.compras.propuestas_compra[propuesta.id].to_dict()
    assert antes == despues


def test_r43_caso_17_agrupacion_devuelve_totales_estimados(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "A")
    core.compras.editar_condiciones_proveedor(p.id, portes=5)
    _asociar(core, "Tomate", p.id, precio_habitual=2.0, unidad_precio="kg")
    _crear_propuesta(core, "Tomate", 3, "kg")

    d = core.compras.agrupar_propuestas_por_proveedor_recomendado()
    assert d["total_grupos"] == 1
    assert d["grupos"][0]["subtotal_estimado"] == 6.0


def test_r43_caso_18_editar_condiciones_proveedor_rechaza_negativos(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "A")

    with pytest.raises(ValueError):
        core.compras.editar_condiciones_proveedor(p.id, portes=-1)


def test_r43_caso_19_editar_asociacion_rechaza_negativos(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "A")
    aso = _asociar(core, "Tomate", p.id)

    with pytest.raises(ValueError):
        core.compras.editar_asociacion_producto_proveedor(aso.id, precio_habitual=-1)


def test_r43_caso_20_pipeline_comparar_proveedores_producto(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "A")
    _asociar(core, "Tomate", p.id, precio_habitual=3.0, unidad_precio="kg")

    r = core.orquestador.resolver(
        SolicitudHostAI(
            "comparar_proveedores_producto_compra",
            {"producto": "Tomate", "cantidad": 2, "unidad": "kg"},
        )
    )
    assert r.ok is True
    assert len(r.datos["comparativa"]) == 1


def test_r43_caso_21_pipeline_comparar_propuesta(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "A")
    _asociar(core, "Tomate", p.id, precio_habitual=3.0, unidad_precio="kg")
    propuesta = _crear_propuesta(core, "Tomate", 2, "kg")

    r = core.orquestador.resolver(
        SolicitudHostAI("comparar_proveedores_propuesta_compra", {"propuesta_id": propuesta.id})
    )
    assert r.ok is True
    assert r.datos["proveedor_recomendado"] == "A"


def test_r43_caso_22_pipeline_editar_condiciones_proveedor(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "A")

    r = core.orquestador.resolver(
        SolicitudHostAI(
            "editar_condiciones_proveedor_compra",
            {"proveedor_id": p.id, "pedido_minimo_importe": 150, "portes": 7},
        )
    )
    assert r.ok is True
    out = core.compras.listar_proveedores(incluir_inactivos=True)
    fila = next(x for x in out if x["id"] == p.id)
    assert fila["pedido_minimo_importe"] == 150.0


def test_r43_caso_23_pipeline_editar_asociacion_comercial(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "A")
    aso = _asociar(core, "Tomate", p.id)

    r = core.orquestador.resolver(
        SolicitudHostAI(
            "editar_asociacion_producto_proveedor_compra",
            {
                "asociacion_id": aso.id,
                "precio_habitual": 2.5,
                "unidad_precio": "kg",
                "plazo_entrega_dias": 2,
            },
        )
    )
    assert r.ok is True
    datos = core.compras.listar_proveedores_producto("Tomate", solo_activos=False)
    assert datos[0]["precio_habitual"] == 2.5


def test_r43_caso_24_desempate_determinista_por_nombre(tmp_path: Path):
    core = HostAICore(tmp_path)
    a = _crear_proveedor(core, "Alpha")
    b = _crear_proveedor(core, "Beta")
    _asociar(core, "Tomate", a.id, precio_habitual=3, unidad_precio="kg")
    _asociar(core, "Tomate", b.id, precio_habitual=3, unidad_precio="kg")

    r1 = core.compras.evaluar_proveedores_producto("Tomate", 1, "kg")
    r2 = core.compras.evaluar_proveedores_producto("Tomate", 1, "kg")
    assert [x["proveedor_id"] for x in r1] == [x["proveedor_id"] for x in r2]


def test_r43_caso_25_mejor_coste_conocido_recibe_ventaja(tmp_path: Path):
    core = HostAICore(tmp_path)
    a = _crear_proveedor(core, "Barato")
    b = _crear_proveedor(core, "Caro")
    _asociar(core, "Tomate", a.id, precio_habitual=1, unidad_precio="kg")
    _asociar(core, "Tomate", b.id, precio_habitual=4, unidad_precio="kg")

    r = core.compras.evaluar_proveedores_producto("Tomate", 1, "kg")
    assert r[0]["proveedor_nombre"] == "Barato"


def test_r43_caso_26_sugerido_inactivo_no_aparece(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "Sugerido")
    core.compras.desactivar_proveedor(p.id)

    r = core.compras.evaluar_proveedores_producto("Producto X", 1, "u", proveedor_sugerido="Sugerido")
    assert r == []


def test_r43_caso_27_recomendar_mantiene_fuente_preferente(tmp_path: Path):
    core = HostAICore(tmp_path)
    a = _crear_proveedor(core, "A")
    _asociar(core, "Tomate", a.id, precio_habitual=2, unidad_precio="kg", preferente=True)

    r = core.compras.recomendar_proveedor("Tomate")
    assert r["fuente"] == "preferente"
    assert r["comparativa"]


def test_r43_caso_28_recomendacion_propuesta_incluye_comparativa(tmp_path: Path):
    core = HostAICore(tmp_path)
    a = _crear_proveedor(core, "A")
    _asociar(core, "Tomate", a.id, precio_habitual=2, unidad_precio="kg")
    propuesta = _crear_propuesta(core, "Tomate", 2, "kg")

    r = core.compras.recomendar_proveedor_para_propuesta(propuesta.id)
    assert isinstance(r.get("comparativa", []), list)
    assert r["proveedor_recomendado"] == "A"


def test_r43_caso_29_generacion_propuesta_recomienda_con_unidad_real(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "KgSupplier")
    _asociar(core, "Arroz", p.id, precio_habitual=2.0, unidad_precio="kg")

    core.produccion_real.listar_planes = lambda: [
        {
            "id": "PLAN-001",
            "nombre": "Plan",
            "estado": "planificado",
            "tareas": [{"receta_id": "REC-1", "cantidad": 1, "titulo": "Tarea"}],
        }
    ]
    core.escandallos_inteligente.calcular_necesidades_receta = lambda _rid, _r, origen="": {
        "necesidades": [
            {
                "nombre": "Arroz",
                "unidad": "kg",
                "articulo_id": "ART-ARROZ",
                "cantidad_bruta": 5,
                "origen": origen or "Plan / Tarea",
                "proveedor_preferente": "",
            }
        ]
    }
    core.stock.stock_actual = lambda: {"items": []}

    d = core.compras.generar_propuesta_compra_inteligente(core)
    assert d["propuestas"][0]["proveedor_sugerido"] == "KgSupplier"


def test_r43_caso_30_consultas_repetidas_no_crean_registros(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "A")
    _asociar(core, "Tomate", p.id, precio_habitual=2, unidad_precio="kg")
    propuesta = _crear_propuesta(core, "Tomate", 2, "kg")

    compras_antes = len(core.compras.compras_registradas)
    for _ in range(5):
        core.compras.recomendar_proveedor_para_propuesta(propuesta.id)
        core.compras.agrupar_propuestas_por_proveedor_recomendado()
        core.compras.listar_propuestas_compra(solo_pendientes=True)
    compras_despues = len(core.compras.compras_registradas)
    assert compras_antes == compras_despues
