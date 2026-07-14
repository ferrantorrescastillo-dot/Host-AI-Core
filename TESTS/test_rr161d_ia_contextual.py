from pathlib import Path

from CORE.host_ai_core import HostAICore


def _core(tmp_path: Path) -> HostAICore:
    base = tmp_path / "host_ai"
    (base / "DATOS" / "diccionarios").mkdir(parents=True)
    (base / "DATOS" / "db").mkdir(parents=True)
    (base / "DATOS" / "diccionarios" / "diccionario_gastronomico_universal.json").write_text("{}", encoding="utf-8")
    return HostAICore(base)


def test_rr161d_entiende_que_preparar_para_la_boda_con_plan_activo(tmp_path):
    core = _core(tmp_path)
    contexto = {"evento_id": "EVT-1", "plan_id": "PLAN-1"}
    r = core.pulido_ia_rr15.procesar("¿Qué tengo que preparar para la boda?", "s1", contexto)
    assert r["intent"] == "consultar_preparacion_evento"
    assert r["pipeline"] == "produccion_real"
    assert r["accion"] == "diagnosticar_plan"
    assert r["parametros"]["plan_id"] == "PLAN-1"
    assert r["propuesta_valida"] is True
    assert r["ejecutado"] is False


def test_rr161d_entiende_rentabilidad_de_esta_boda(tmp_path):
    core = _core(tmp_path)
    r = core.pulido_ia_rr15.procesar(
        "¿Cuánto voy a ganar con esta boda?", "s2", {"evento_id": "EVT-2"}
    )
    assert r["intent"] == "consultar_rentabilidad"
    assert r["pipeline"] == "costes"
    assert r["parametros"]["evento_id"] == "EVT-2"
    assert r["propuesta_valida"] is True


def test_rr161d_entiende_resumen_del_evento_activo(tmp_path):
    core = _core(tmp_path)
    r = core.pulido_ia_rr15.procesar("¿Cómo va la boda?", "s3", {"evento_id": "EVT-3"})
    assert r["intent"] == "consultar_evento_activo"
    assert r["pipeline"] == "evento"
    assert r["accion"] == "diagnosticar"
    assert r["parametros"]["evento_id"] == "EVT-3"
    assert r["propuesta_valida"] is True


def test_rr161d_sigue_siendo_modo_seguro(tmp_path):
    core = _core(tmp_path)
    antes = len(core.eventos.listar_eventos())
    r = core.pulido_ia_rr15.procesar("¿Qué tengo que preparar para la boda?", "s4", {"plan_id": "PLAN-X"})
    despues = len(core.eventos.listar_eventos())
    assert antes == despues == 0
    assert r["ejecutado"] is False
