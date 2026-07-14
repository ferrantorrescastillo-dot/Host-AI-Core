from pathlib import Path

from CORE.host_ai_core import HostAICore


def _core(tmp_path: Path) -> HostAICore:
    base = tmp_path / "host_ai"
    (base / "DATOS" / "diccionarios").mkdir(parents=True)
    (base / "DATOS" / "db").mkdir(parents=True)
    (base / "DATOS" / "diccionarios" / "diccionario_gastronomico_universal.json").write_text("{}", encoding="utf-8")
    return HostAICore(base)


def test_rr15_respuesta_stock_natural_y_segura(tmp_path):
    core = _core(tmp_path)
    r = core.pulido_ia_rr15.procesar("¿Qué stock tengo?")
    assert r["propuesta_valida"] is True
    assert "consultar el stock actual" in r["respuesta"].lower()
    assert "no modifica datos" in r["respuesta"].lower()
    assert r["ejecutado"] is False


def test_rr15_compra_multiturno_pregunta_solo_lo_que_falta(tmp_path):
    core = _core(tmp_path)
    r1 = core.pulido_ia_rr15.procesar("Necesito comprar tomates", "c1")
    assert "cantidad" in r1["respuesta"].lower()
    r2 = core.pulido_ia_rr15.procesar("5 kg de Sarda", "c1")
    assert r2["propuesta_valida"] is True
    assert "necesidad de compra" in r2["respuesta"].lower()
    assert "confirmación" in r2["respuesta"].lower()
    assert r2["parametros"]["cantidad"] == 5


def test_rr15_reutiliza_evento_activo_sin_preguntar_otro_id(tmp_path):
    core = _core(tmp_path)
    contexto = {"evento_id": "EVT-ACTIVO-1"}
    r = core.pulido_ia_rr15.procesar("Calcula el coste del evento", "e1", contexto)
    assert r["propuesta_valida"] is True
    assert r["parametros"]["evento_id"] == "EVT-ACTIVO-1"
    assert "me falta" not in r["respuesta"].lower()


def test_rr15_error_general_da_ejemplos_utiles(tmp_path):
    core = _core(tmp_path)
    r = core.pulido_ia_rr15.procesar("hola qué tal", "g1")
    assert r["propuesta_valida"] is False
    assert "qué stock tengo" in r["respuesta"].lower()
    assert "boda" in r["respuesta"].lower()


def test_rr15_no_ejecuta_cambios(tmp_path):
    core = _core(tmp_path)
    antes = len(core.eventos.listar_eventos())
    r = core.pulido_ia_rr15.procesar("Tengo una boda para 40 personas mañana a las 14:00")
    despues = len(core.eventos.listar_eventos())
    assert r["propuesta_valida"] is True
    assert antes == despues == 0
    assert r["ejecutado"] is False
