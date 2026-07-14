from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from SERVICIOS.bandeja_trabajo_piloto_11 import BandejaTrabajoPiloto11
from SERVICIOS.jornada_piloto_12 import JornadaPiloto12


def preparar(tmp_path: Path):
    db = tmp_path / "DATOS" / "db"
    db.mkdir(parents=True)
    planes = [{"id":"P1","evento_id":"E1","tareas":[
        {"id":"TP1","titulo":"Demi-glace","estado_ejecucion":"pendiente","prioridad":90,"fases":[
            {"duracion_min":30,"tipo":"preparacion"},{"duracion_min":120,"tipo":"coccion"}]},
        {"id":"TP2","titulo":"Carrillera","estado_ejecucion":"pendiente","prioridad":80,"fases":[
            {"duracion_min":45,"tipo":"preparacion"}]},
    ]}]
    (db/"planes_produccion.json").write_text(json.dumps(planes),encoding="utf-8")
    (db/"eventos.json").write_text(json.dumps([{"id":"E1","nombre":"Boda","fecha":"14/07/2026","pax":100,"estado":"pendiente"}]),encoding="utf-8")
    (db/"compras_pedidos.json").write_text("[]",encoding="utf-8")
    return BandejaTrabajoPiloto11(tmp_path)


def test_prioridades_humanas_y_orden(tmp_path):
    b=preparar(tmp_path)
    b.crear_tarea("Recepción Makro","RECEPCION",90)
    j=JornadaPiloto12(tmp_path,b).construir(datetime(2026,7,13,8,0))
    assert j["resumen"]["muy_urgentes"] >= 2
    assert j["tareas"][0]["prioridad_codigo"] == "MUY_URGENTE"
    assert j["solo_lectura"] is True


def test_tiempos_activos_pasivos(tmp_path):
    b=preparar(tmp_path)
    j=JornadaPiloto12(tmp_path,b).construir(datetime(2026,7,13,8,0))
    assert j["tiempos"]["pasivo_conocido_min"] == 120
    assert j["tiempos"]["activo_conocido_min"] >= 75
    assert any(x.get("duracion_pasiva_min") == 120 for x in j["tareas"])


def test_recomendacion_paralela(tmp_path):
    b=preparar(tmp_path)
    j=JornadaPiloto12(tmp_path,b).construir(datetime(2026,7,13,8,0))
    assert any("durante los 120 min pasivos" in x["motivo"] for x in j["recomendaciones"])


def test_no_modifica_fuentes(tmp_path):
    b=preparar(tmp_path)
    paths=[tmp_path/"DATOS/db/planes_produccion.json",tmp_path/"DATOS/db/eventos.json"]
    before=[p.read_bytes() for p in paths]
    JornadaPiloto12(tmp_path,b).construir(datetime(2026,7,13,8,0))
    assert before == [p.read_bytes() for p in paths]


def test_diagnostico(tmp_path):
    d=JornadaPiloto12(tmp_path).diagnostico()
    assert d["diagnostico"] == "OK"
    assert d["solo_lectura"] is True
    assert d["tiempo_pasivo_min"] == 120
