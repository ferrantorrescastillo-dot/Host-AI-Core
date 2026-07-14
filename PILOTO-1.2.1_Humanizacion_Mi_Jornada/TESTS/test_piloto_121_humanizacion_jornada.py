from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from SERVICIOS.bandeja_trabajo_piloto_11 import BandejaTrabajoPiloto11
from SERVICIOS.jornada_piloto_12 import JornadaPiloto12


def preparar(tmp_path: Path, fecha_evento="14/07/2026"):
    db = tmp_path / "DATOS" / "db"; db.mkdir(parents=True)
    planes=[{"id":"P1","evento_id":"E1","tareas":[{"id":"TP1","titulo":"Demi-glace","estado_ejecucion":"pendiente","prioridad":90,"fases":[{"duracion_min":25,"tipo":"preparacion"},{"duracion_min":240,"tipo":"coccion"}]}]}]
    (db/"planes_produccion.json").write_text(json.dumps(planes),encoding="utf-8")
    (db/"eventos.json").write_text(json.dumps([{"id":"E1","nombre":"Boda","fecha":fecha_evento,"pax":100,"estado":"pendiente"}]),encoding="utf-8")
    (db/"compras_pedidos.json").write_text("[]",encoding="utf-8")
    return BandejaTrabajoPiloto11(tmp_path)


def test_humaniza_duracion_prioridad_y_saludo(tmp_path):
    j=JornadaPiloto12(tmp_path, preparar(tmp_path)).construir(datetime(2026,7,13,8,0))
    prod=next(x for x in j["tareas"] if x["tipo"]=="PRODUCCION")
    assert prod["duracion_humana"] == "4 h 25 min"
    assert prod["prioridad_humana"] == "🔴 Muy urgente"
    assert j["saludo"].startswith("Buenos días")
    assert j["version"] == "PILOTO-1.2.1"


def test_evento_pasado_se_exprime_en_lenguaje_natural(tmp_path):
    j=JornadaPiloto12(tmp_path, preparar(tmp_path,"10/07/2026")).construir(datetime(2026,7,13,8,0))
    prod=next(x for x in j["tareas"] if x["tipo"]=="PRODUCCION")
    assert "ya ha pasado" in prod["evento_mensaje"]
    assert "-3" not in prod["evento_mensaje"]


def test_resumen_jornada_vacia(tmp_path):
    (tmp_path/"DATOS/db").mkdir(parents=True)
    for n in ("planes_produccion.json","eventos.json","compras_pedidos.json"):
        (tmp_path/"DATOS/db"/n).write_text("[]",encoding="utf-8")
    j=JornadaPiloto12(tmp_path).construir(datetime(2026,7,13,21,0))
    assert j["resumen"]["abiertas"] == 0
    assert "jornada está limpia" in j["resumen_humano"]
    assert j["cronograma"] == []


def test_cronograma_es_legible_y_no_modifica_fuentes(tmp_path):
    b=preparar(tmp_path)
    paths=[tmp_path/"DATOS/db/planes_produccion.json",tmp_path/"DATOS/db/eventos.json"]
    before=[p.read_bytes() for p in paths]
    j=JornadaPiloto12(tmp_path,b).construir(datetime(2026,7,13,8,0))
    assert j["cronograma"][0]["franja"] == "08:00–08:25"
    assert before == [p.read_bytes() for p in paths]


def test_no_muestra_minutos_tecnicos_en_recomendacion_paralela(tmp_path):
    b=preparar(tmp_path); b.crear_tarea("Recepción Makro","RECEPCION",80)
    j=JornadaPiloto12(tmp_path,b).construir(datetime(2026,7,13,8,0))
    paralela=next(x for x in j["recomendaciones"] if x.get("paralela_con"))
    assert "4 h" in paralela["motivo_humano"]
    assert "240 min" not in paralela["motivo_humano"]
