from pathlib import Path

from CORE.host_ai_core import HostAICore
from SERVICIOS.jornada_piloto_12 import JornadaPiloto12
from SERVICIOS.recepcion_operativa_rp3 import RecepcionOperativaRP3


def _crear_pedido_base(core: HostAICore):
    n1 = core.compras.registrar_necesidad(
        "Tomate pera", 10, "kg", proveedor_preferente="Makro", articulo_id="ART-TOMATE"
    )
    n2 = core.compras.registrar_necesidad(
        "Aceite oliva", 5, "L", proveedor_preferente="Makro", articulo_id="ART-ACEITE"
    )
    generado = core.compras.generar_pedidos_sugeridos()
    pedido_id = generado["pedidos_sugeridos"][0]["id"]
    return pedido_id, n1.id, n2.id


def _servicio(tmp_path: Path):
    core = HostAICore(tmp_path)
    svc = RecepcionOperativaRP3(core)
    return core, svc


def test_rp3_recepcion_correcta_actualiza_stock_lotes_movimientos_y_pedido(tmp_path: Path):
    core, svc = _servicio(tmp_path)
    pedido_id, _, _ = _crear_pedido_base(core)

    sesion = svc.iniciar_recepcion(pedido_id, "Makro")
    for linea in sesion["lineas_esperadas"]:
        svc.actualizar_linea_esperada(
            sesion["id"], linea["linea_id"],
            cantidad_recibida=linea["cantidad_esperada"],
            unidad_recibida=linea["unidad_esperada"],
            precio_recibido=1.5,
            lote="LOTE-MAKRO-01",
            caducidad="2026-12-31",
            estado_linea="aceptada",
        )

    out = svc.finalizar_recepcion(sesion["id"], "RECEPCIONAR")
    assert out["ok"] is True
    assert out["estado"] == "APLICADA"

    pedido = core.compras.obtener_pedido(pedido_id)
    assert pedido is not None
    assert pedido.estado == "recibido"

    stock = core.stock.stock_actual()
    assert stock["total_lotes"] >= 2
    assert any(m.get("tipo") == "entrada" for m in core.stock.movimientos_listado())



def test_rp3_pedido_parcial_y_no_recibido_genera_incidencias_y_no_cierra_pedido(tmp_path: Path):
    core, svc = _servicio(tmp_path)
    pedido_id, _, _ = _crear_pedido_base(core)

    sesion = svc.iniciar_recepcion(pedido_id, "Makro")
    l1, l2 = sesion["lineas_esperadas"]

    svc.actualizar_linea_esperada(
        sesion["id"], l1["linea_id"],
        cantidad_recibida=4,
        unidad_recibida=l1["unidad_esperada"],
        precio_recibido=l1["precio_esperado"],
        estado_linea="parcial",
        motivo="Falta palet",
    )
    svc.actualizar_linea_esperada(
        sesion["id"], l2["linea_id"],
        cantidad_recibida=0,
        unidad_recibida=l2["unidad_esperada"],
        precio_recibido=l2["precio_esperado"],
        estado_linea="no_recibida",
        motivo="No llegó",
    )

    out = svc.finalizar_recepcion(sesion["id"], "RECEPCIONAR")
    assert out["ok"] is True
    assert len(out["registro"].get("incidencias", [])) >= 2

    pedido = core.compras.obtener_pedido(pedido_id)
    assert pedido is not None
    assert pedido.estado in {"borrador", "preparado", "enviado"}



def test_rp3_producto_rechazado_y_precio_diferente(tmp_path: Path):
    core, svc = _servicio(tmp_path)
    pedido_id, _, _ = _crear_pedido_base(core)

    sesion = svc.iniciar_recepcion(pedido_id, "Makro")
    l1, l2 = sesion["lineas_esperadas"]
    svc.actualizar_linea_esperada(
        sesion["id"], l1["linea_id"],
        cantidad_recibida=l1["cantidad_esperada"],
        unidad_recibida=l1["unidad_esperada"],
        precio_recibido=2.25,
        estado_linea="aceptada",
        motivo="Subida de tarifa",
    )
    svc.actualizar_linea_esperada(
        sesion["id"], l2["linea_id"],
        cantidad_recibida=0,
        unidad_recibida=l2["unidad_esperada"],
        precio_recibido=l2["precio_esperado"],
        estado_linea="rechazada",
        motivo="Producto roto",
    )

    out = svc.finalizar_recepcion(sesion["id"], "RECEPCIONAR")
    assert out["ok"] is True
    tipos = {x.get("tipo") for x in out["registro"].get("incidencias", [])}
    assert "precio_incorrecto" in tipos
    assert "producto_rechazado" in tipos



def test_rp3_sustitucion_adicional_lote_caducidad(tmp_path: Path):
    core, svc = _servicio(tmp_path)
    pedido_id, _, _ = _crear_pedido_base(core)

    sesion = svc.iniciar_recepcion(pedido_id, "Makro")
    l1, l2 = sesion["lineas_esperadas"]

    svc.actualizar_linea_esperada(
        sesion["id"], l1["linea_id"],
        cantidad_recibida=l1["cantidad_esperada"],
        unidad_recibida=l1["unidad_esperada"],
        precio_recibido=1.8,
        lote="TOM-2026-01",
        caducidad="2026-11-15",
        estado_linea="aceptada",
    )
    svc.actualizar_linea_esperada(
        sesion["id"], l2["linea_id"],
        cantidad_recibida=5,
        unidad_recibida=l2["unidad_esperada"],
        precio_recibido=4.7,
        estado_linea="sustitucion",
        articulo_id_recibido="ART-AOVE-ALT",
        nombre_recibido="Aceite oliva virgen extra",
        lote="AOV-2026-ALT",
        caducidad="2027-01-01",
    )
    svc.registrar_adicional(
        sesion["id"],
        nombre="Vinagre",
        cantidad=2,
        unidad="L",
        precio_unitario=1.2,
        articulo_id="ART-VINAGRE",
        lote="VIN-01",
        caducidad="2027-02-01",
        motivo="Extra oferta",
    )

    out = svc.finalizar_recepcion(sesion["id"], "RECEPCIONAR")
    assert out["ok"] is True
    assert len(out["registro"].get("entradas_stock", [])) == 3

    lotes = core.stock.lotes_listado("", solo_con_stock=True)
    assert any(l.get("caducidad") == "2026-11-15" for l in lotes)
    assert any(l.get("id", "").startswith("LOTE-") for l in lotes)



def test_rp3_no_acepta_cantidad_negativa_ni_unidad_incompatible(tmp_path: Path):
    _core, svc = _servicio(tmp_path)
    pedido_id, _, _ = _crear_pedido_base(_core)
    sesion = svc.iniciar_recepcion(pedido_id, "Makro")
    linea = sesion["lineas_esperadas"][0]

    try:
        svc.actualizar_linea_esperada(
            sesion["id"], linea["linea_id"],
            cantidad_recibida=-1,
            unidad_recibida=linea["unidad_esperada"],
            estado_linea="aceptada",
        )
    except ValueError as exc:
        assert "negativas" in str(exc)
    else:
        assert False

    # Unidad incompatible en commit para linea esperada no-sustitucion.
    svc.actualizar_linea_esperada(
        sesion["id"], linea["linea_id"],
        cantidad_recibida=linea["cantidad_esperada"],
        unidad_recibida="ud",
        precio_recibido=1.0,
        estado_linea="aceptada",
    )
    for otra in sesion["lineas_esperadas"][1:]:
        svc.actualizar_linea_esperada(
            sesion["id"], otra["linea_id"],
            cantidad_recibida=otra["cantidad_esperada"],
            unidad_recibida=otra["unidad_esperada"],
            estado_linea="aceptada",
        )
    out = svc.finalizar_recepcion(sesion["id"], "RECEPCIONAR")
    assert out["ok"] is False
    assert out["estado"] == "ERROR_REVERTIDO"



def test_rp3_rollback_y_persistencia(tmp_path: Path):
    core, svc = _servicio(tmp_path)
    pedido_id, _, _ = _crear_pedido_base(core)

    sesion = svc.iniciar_recepcion(pedido_id, "Makro")
    for linea in sesion["lineas_esperadas"]:
        svc.actualizar_linea_esperada(
            sesion["id"], linea["linea_id"],
            cantidad_recibida=linea["cantidad_esperada"],
            unidad_recibida=linea["unidad_esperada"],
            estado_linea="aceptada",
        )

    lotes_antes = len(core.stock.lotes)
    movimientos_antes = len(core.stock.movimientos)

    original = core.stock.registrar_entrada

    def _falla_una(*args, **kwargs):
        raise RuntimeError("fallo forzado rp3")

    core.stock.registrar_entrada = _falla_una
    try:
        out = svc.finalizar_recepcion(sesion["id"], "RECEPCIONAR")
    finally:
        core.stock.registrar_entrada = original

    assert out["ok"] is False
    assert len(core.stock.lotes) == lotes_antes
    assert len(core.stock.movimientos) == movimientos_antes

    # Persistencia caso correcto.
    sesion2 = svc.iniciar_recepcion(pedido_id, "Makro")
    for linea in sesion2["lineas_esperadas"]:
        svc.actualizar_linea_esperada(
            sesion2["id"], linea["linea_id"],
            cantidad_recibida=linea["cantidad_esperada"],
            unidad_recibida=linea["unidad_esperada"],
            estado_linea="aceptada",
        )
    ok = svc.finalizar_recepcion(sesion2["id"], "RECEPCIONAR")
    assert ok["ok"] is True

    core2 = HostAICore(tmp_path)
    svc2 = RecepcionOperativaRP3(core2)
    abiertos = svc2.listar_sesiones_abiertas()
    assert isinstance(abiertos, list)
    assert core2.compras.obtener_pedido(pedido_id).estado == "recibido"



def test_rp3_briefing_actualizado_y_caso_completo_controlado(tmp_path: Path):
    core, svc = _servicio(tmp_path)
    pedido_id, _, _ = _crear_pedido_base(core)

    sesion = svc.iniciar_recepcion(pedido_id, "Makro")
    stock_antes = core.stock.stock_actual()

    l1, l2 = sesion["lineas_esperadas"]
    svc.actualizar_linea_esperada(
        sesion["id"], l1["linea_id"],
        cantidad_recibida=l1["cantidad_esperada"],
        unidad_recibida=l1["unidad_esperada"],
        precio_recibido=1.9,
        lote="L1",
        caducidad="2026-10-10",
        estado_linea="aceptada",
    )
    svc.actualizar_linea_esperada(
        sesion["id"], l2["linea_id"],
        cantidad_recibida=2,
        unidad_recibida=l2["unidad_esperada"],
        precio_recibido=5.1,
        estado_linea="parcial",
        motivo="Faltan cajas",
    )
    svc.registrar_adicional(
        sesion["id"],
        nombre="Sal fina",
        cantidad=1,
        unidad="kg",
        precio_unitario=0.8,
        articulo_id="ART-SAL",
        lote="SAL-1",
        caducidad="2027-01-01",
        motivo="Adicional",
    )

    preview = svc.preparar_validacion(sesion["id"])
    assert preview["pedido_id"] == pedido_id
    assert len(preview["diferencias"]) >= 2

    out = svc.finalizar_recepcion(sesion["id"], "RECEPCIONAR")
    assert out["ok"] is True
    stock_despues = out["stock_despues"]
    assert stock_despues["total_lotes"] > stock_antes["total_lotes"]

    jornada = JornadaPiloto12(tmp_path).construir()
    briefing = jornada["briefing_apertura"]
    rp3 = briefing.get("recepciones_rp3") or {}
    assert rp3.get("recepciones_hoy", 0) >= 1
    assert rp3.get("lineas_recibidas_hoy", 0) >= 1
