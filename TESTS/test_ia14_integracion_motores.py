from pathlib import Path

from CORE.host_ai_core import HostAICore


def _core(tmp_path: Path) -> HostAICore:
    base = tmp_path / "host_ai"
    (base / "DATOS" / "diccionarios").mkdir(parents=True)
    (base / "DATOS" / "db").mkdir(parents=True)
    (base / "DATOS" / "diccionarios" / "diccionario_gastronomico_universal.json").write_text("{}", encoding="utf-8")
    return HostAICore(base)


def test_consulta_stock_prepara_contrato_seguro(tmp_path):
    core = _core(tmp_path)
    r = core.integracion_motores_ia14.analizar("¿Qué stock tengo?")
    assert r["propuesta_valida"] is True
    assert r["pipeline"] == "stock"
    assert r["accion"] == "stock_actual"
    assert r["tipo_operacion"] == "consulta"
    assert r["requiere_confirmacion"] is False
    assert r["ejecutado"] is False


def test_compra_multiturno_traduce_parametros_y_pide_confirmacion(tmp_path):
    core = _core(tmp_path)
    r1 = core.integracion_motores_ia14.analizar("Necesito comprar tomates", "compras")
    assert r1["estado"] == "esperando_dato"
    r2 = core.integracion_motores_ia14.analizar("5 kg de Sarda", "compras")
    assert r2["propuesta_valida"] is True
    assert r2["pipeline"] == "compras"
    assert r2["accion"] == "registrar_necesidad"
    assert r2["parametros"]["nombre"].lower() == "tomates"
    assert r2["parametros"]["cantidad"] == 5
    assert r2["parametros"]["unidad"].lower() == "kg"
    assert r2["requiere_confirmacion"] is True
    assert r2["ejecutado"] is False


def test_evento_completo_prepara_pipeline_real(tmp_path):
    core = _core(tmp_path)
    r = core.integracion_motores_ia14.analizar(
        "Tengo una boda para 80 personas el 22/10/2026 a las 13:30"
    )
    assert r["propuesta_valida"] is True
    assert r["pipeline"] == "evento"
    assert r["accion"] == "crear"
    assert r["parametros"]["pax"] == 80
    assert r["parametros"]["fecha"] == "2026-10-22"
    assert r["parametros"]["hora_inicio"] == "13:30"
    assert r["requiere_confirmacion"] is True


def test_contrato_se_valida_con_registro_real(tmp_path):
    core = _core(tmp_path)
    r = core.integracion_motores_ia14.analizar("Haz el pedido")
    assert r["pipeline_existe"] is True
    assert r["accion_soportada"] is True
    assert r["puede_ejecutarse_en_ia2"] is True
    assert r["ejecutado"] is False


def test_no_ejecuta_ni_modifica_datos(tmp_path):
    core = _core(tmp_path)
    antes = len(core.eventos.listar_eventos())
    r = core.integracion_motores_ia14.analizar(
        "Tengo una boda para 50 personas mañana a las 14:00"
    )
    despues = len(core.eventos.listar_eventos())
    assert r["propuesta_valida"] is True
    assert antes == despues == 0
