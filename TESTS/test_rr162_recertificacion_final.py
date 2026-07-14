from pathlib import Path
from types import SimpleNamespace

from APP.consola import AppConsolaHostAI
from CORE.host_ai_core import HostAICore


def _core(tmp_path: Path) -> HostAICore:
    base = tmp_path / "host_ai_rr162"
    (base / "DATOS" / "diccionarios").mkdir(parents=True)
    (base / "DATOS" / "db").mkdir(parents=True)
    (base / "DATOS" / "diccionarios" / "diccionario_gastronomico_universal.json").write_text(
        "{}", encoding="utf-8"
    )
    return HostAICore(base)


def test_rr162_cadena_contexto_costes_compras_stock_e_ia(tmp_path):
    """Puerta automática mínima de Restaurant Ready tras RR1.6.1 A-D."""
    core = _core(tmp_path)
    app = AppConsolaHostAI(core)

    # El contexto debe persistir entre instancias de consola.
    app.ultimo_evento_id = "EVT-RR162"
    app.ultimo_plan_produccion_id = "PLAN-RR162"
    app.ultimo_pedido_compra_id = "PED-RR162"
    app.ultimo_escandallo_id = "REC-RR162"

    reiniciada = AppConsolaHostAI(SimpleNamespace(base_dir=core.base_dir))
    assert reiniciada.ultimo_evento_id == "EVT-RR162"
    assert reiniciada.ultimo_plan_produccion_id == "PLAN-RR162"
    assert reiniciada.ultimo_pedido_compra_id == "PED-RR162"
    assert reiniciada.ultimo_escandallo_id == "REC-RR162"

    # La IA contextual debe preparar la consulta correcta sin ejecutar cambios.
    antes = len(core.eventos.listar_eventos())
    respuesta = core.pulido_ia_rr15.procesar(
        "¿Qué tengo que preparar para la boda?",
        "rr162",
        {"evento_id": "EVT-RR162", "plan_id": "PLAN-RR162"},
    )
    despues = len(core.eventos.listar_eventos())

    assert respuesta["intent"] == "consultar_preparacion_evento"
    assert respuesta["pipeline"] == "produccion_real"
    assert respuesta["parametros"]["plan_id"] == "PLAN-RR162"
    assert respuesta["propuesta_valida"] is True
    assert respuesta["ejecutado"] is False
    assert antes == despues == 0
