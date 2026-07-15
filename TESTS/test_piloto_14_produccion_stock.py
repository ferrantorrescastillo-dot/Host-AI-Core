from pathlib import Path
import copy

from CORE.host_ai_core import HostAICore
from MODELOS.produccion_real import TareaProduccionReal
from SERVICIOS.produccion_stock_piloto_14 import ProduccionStockPiloto14


def crear_core(tmp_path: Path, stock_harina=10.0):
    core = HostAICore(tmp_path)
    core.db.guardar("escandallos", [{
        "receta_id": "REC-PAN", "nombre": "Pan", "raciones_base": 10,
        "lineas": [{"nombre": "Harina", "cantidad": 2.0, "cantidad_bruta": 2.0, "unidad": "kg", "tipo": "articulo", "articulo_id": "ART-HARINA"}],
    }])
    core.stock.registrar_entrada("Harina", stock_harina, "kg", articulo_id="ART-HARINA")
    plan = core.produccion_real.crear_plan_manual("Producción diaria", responsable="Ferran", estado="planificado")
    tarea = TareaProduccionReal(titulo="Pan", receta_id="REC-PAN", receta="Pan", cantidad=20, unidad="u")
    core.produccion_real.planes[plan["id"]].tareas.append(tarea)
    core.produccion_real._persistir()
    return core, plan["id"], tarea.id


def test_previsualiza_consumos_escalados(tmp_path):
    core, plan_id, tarea_id = crear_core(tmp_path)
    vista = ProduccionStockPiloto14(core).preparar_cierre(plan_id, tarea_id)
    assert vista["ok"] is True
    assert vista["consumos"][0]["cantidad"] == 4.0
    assert vista["produccion_generada"]["cantidad"] == 20.0


def test_cierra_produccion_actualiza_stock_y_trazabilidad(tmp_path):
    core, plan_id, tarea_id = crear_core(tmp_path)
    servicio = ProduccionStockPiloto14(core)
    resultado = servicio.cerrar_y_actualizar_stock(plan_id, tarea_id, "Ferran", "L-001")
    assert resultado["ok"] is True
    harina = next(x for x in core.stock.stock_actual()["items"] if x["articulo_id"] == "ART-HARINA")
    pan = next(x for x in core.stock.stock_actual()["items"] if x["articulo_id"] == "REC-PAN")
    assert harina["cantidad"] == 6.0
    assert pan["cantidad"] == 20.0
    assert core.produccion_real.estado_tarea(plan_id, tarea_id)["estado_ejecucion"] == "finalizada"
    assert servicio.historial()[0]["lote"] == "L-001"


def test_bloquea_si_falta_stock_sin_escrituras(tmp_path):
    core, plan_id, tarea_id = crear_core(tmp_path, stock_harina=1.0)
    antes = core.stock.stock_actual()
    resultado = ProduccionStockPiloto14(core).cerrar_y_actualizar_stock(plan_id, tarea_id)
    assert resultado["estado"] == "STOCK_INSUFICIENTE"
    assert resultado["faltantes"][0]["faltante"] == 3.0
    assert core.stock.stock_actual() == antes
    assert core.produccion_real.estado_tarea(plan_id, tarea_id)["estado_ejecucion"] == "pendiente"


def test_impide_registro_duplicado(tmp_path):
    core, plan_id, tarea_id = crear_core(tmp_path)
    servicio = ProduccionStockPiloto14(core)
    assert servicio.cerrar_y_actualizar_stock(plan_id, tarea_id)["ok"] is True
    segundo = servicio.preparar_cierre(plan_id, tarea_id)
    assert segundo["estado"] == "YA_REGISTRADA"
    assert len(servicio.historial()) == 1


def test_sin_escandallo_no_finaliza(tmp_path):
    core, plan_id, tarea_id = crear_core(tmp_path)
    core.db.guardar("escandallos", [])
    resultado = ProduccionStockPiloto14(core).cerrar_y_actualizar_stock(plan_id, tarea_id)
    assert resultado["estado"] == "SIN_ESCANDALLO"
    assert core.produccion_real.estado_tarea(plan_id, tarea_id)["estado_ejecucion"] == "pendiente"


def test_registra_incidencia_bloqueante(tmp_path):
    core, plan_id, tarea_id = crear_core(tmp_path, stock_harina=1.0)
    resultado = ProduccionStockPiloto14(core).registrar_incidencia_stock(plan_id, tarea_id, "Falta harina")
    assert resultado["ok"] is True
    assert core.produccion_real.estado_tarea(plan_id, tarea_id)["bloqueo"] == "Falta harina"


def test_genera_movimiento_transformacion_y_trazabilidad(tmp_path):
    core, plan_id, tarea_id = crear_core(tmp_path)
    servicio = ProduccionStockPiloto14(core)
    resultado = servicio.cerrar_y_actualizar_stock(plan_id, tarea_id, "Ferran", "L-TRAZA-01")
    assert resultado["ok"] is True
    movs = list(core.stock.movimientos.values())
    tipos = {m.tipo for m in movs}
    assert {"salida", "entrada", "transformacion"}.issubset(tipos)
    transform = next(m for m in movs if m.tipo == "transformacion")
    assert transform.trazabilidad.get("lote_generado")
    assert isinstance(transform.trazabilidad.get("movimientos_salida"), list)
    assert transform.trazabilidad.get("usuario") in {"Ferran", "cocina"}


def test_unidad_incompatible_bloquea_cierre(tmp_path):
    core, plan_id, tarea_id = crear_core(tmp_path)
    # Convertimos el único lote a gramos para forzar incompatibilidad de unidad.
    lote = next(iter(core.stock.lotes.values()))
    lote.unidad = "g"
    core.stock._guardar_automatico()

    vista = ProduccionStockPiloto14(core).preparar_cierre(plan_id, tarea_id)
    assert vista["ok"] is False
    assert vista["estado"] == "UNIDAD_INCOMPATIBLE"


def test_ap_como_mp_no_permitido(tmp_path):
    core, plan_id, tarea_id = crear_core(tmp_path)
    core.db.guardar("escandallos", [{
        "receta_id": "REC-PAN",
        "nombre": "Pan",
        "raciones_base": 10,
        "lineas": [{"nombre": "A.P Salsa base", "cantidad": 2.0, "cantidad_bruta": 2.0, "unidad": "kg", "tipo": "articulo", "articulo_id": "A.P-001"}],
    }])
    vista = ProduccionStockPiloto14(core).preparar_cierre(plan_id, tarea_id)
    assert vista["ok"] is False
    assert vista["estado"] == "AP_COMO_MP_NO_PERMITIDO"


def test_receta_incompleta_bloquea_cierre(tmp_path):
    core, plan_id, tarea_id = crear_core(tmp_path)
    core.db.guardar("escandallos", [{
        "receta_id": "REC-PAN",
        "nombre": "Pan",
        "raciones_base": 10,
        "lineas": [{"nombre": "Harina", "cantidad": 0, "cantidad_bruta": 0, "unidad": "kg", "tipo": "articulo", "articulo_id": "ART-HARINA"}],
    }])
    vista = ProduccionStockPiloto14(core).preparar_cierre(plan_id, tarea_id)
    assert vista["ok"] is False
    assert vista["estado"] == "RECETA_INCOMPLETA"


def test_rollback_si_falla_entrada(tmp_path):
    core, plan_id, tarea_id = crear_core(tmp_path)
    servicio = ProduccionStockPiloto14(core)
    lotes_antes = copy.deepcopy(core.stock.lotes)
    movimientos_antes = copy.deepcopy(core.stock.movimientos)

    original = core.stock.registrar_entrada
    def _falla_entrada(*args, **kwargs):
        raise RuntimeError("fallo forzado entrada")
    core.stock.registrar_entrada = _falla_entrada

    try:
        resultado = servicio.cerrar_y_actualizar_stock(plan_id, tarea_id)
    finally:
        core.stock.registrar_entrada = original

    assert resultado["ok"] is False
    assert resultado["estado"] == "ERROR_REVERTIDO"
    assert core.stock.lotes.keys() == lotes_antes.keys()
    assert core.stock.movimientos.keys() == movimientos_antes.keys()
    assert core.produccion_real.estado_tarea(plan_id, tarea_id)["estado_ejecucion"] == "pendiente"
