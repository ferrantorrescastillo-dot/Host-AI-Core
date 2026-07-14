from __future__ import annotations

import json
from pathlib import Path

from SERVICIOS.bandeja_trabajo_piloto_11 import BandejaTrabajoPiloto11


def test_bandeja_ciclo_completo(tmp_path: Path):
    service = BandejaTrabajoPiloto11(tmp_path)
    task = service.crear_tarea("Actualizar stock", "STOCK", 80)
    assert service.resumen()["abiertas"] == 1
    service.cambiar_estado(task["id"], "EN_CURSO")
    assert service.obtener(task["id"])["estado"] == "EN_CURSO"
    service.cambiar_estado(task["id"], "APLAZADA", "Final del día", "20:00")
    assert service.obtener(task["id"])["aplazado_hasta"] == "20:00"
    service.cambiar_estado(task["id"], "COMPLETADA")
    assert service.resumen()["completadas"] == 1


def test_recepcion_pendiente_no_duplica(tmp_path: Path):
    service = BandejaTrabajoPiloto11(tmp_path)
    plan = {"plan_id": "REC-1", "estado": "LISTA_PARA_CONFIRMAR", "proveedor": "Makro"}
    a = service.registrar_recepcion_pendiente(plan)
    b = service.registrar_recepcion_pendiente(plan)
    assert a["id"] == b["id"]
    assert service.resumen()["total"] == 1


def test_sincroniza_produccion_eventos_y_pedidos(tmp_path: Path):
    db = tmp_path / "DATOS" / "db"
    db.mkdir(parents=True)
    (db / "planes_produccion.json").write_text(json.dumps([{
        "id":"PLAN-1","evento":"Boda","evento_id":"EVT-1","tareas":[{"id":"TP-1","titulo":"Hacer salsa","prioridad":90,"estado_ejecucion":"pendiente"}]
    }]), encoding="utf-8")
    (db / "eventos.json").write_text(json.dumps([{"id":"EVT-1","nombre":"Boda","fecha":"2026-08-01","pax":100,"estado":"pendiente"}]), encoding="utf-8")
    (db / "compras_pedidos.json").write_text(json.dumps([{"id":"PED-1","proveedor":"Makro","estado":"borrador","lineas":[]}]), encoding="utf-8")
    service = BandejaTrabajoPiloto11(tmp_path)
    assert service.sincronizar_fuentes() == 3
    assert service.sincronizar_fuentes() == 0
    assert service.resumen()["abiertas"] == 3


def test_diagnostico_aislado(tmp_path: Path):
    service = BandejaTrabajoPiloto11(tmp_path)
    result = service.diagnostico()
    assert result["diagnostico"] == "OK"
    assert result["integridad"] == "OK"
    assert result["tareas"] == 2
