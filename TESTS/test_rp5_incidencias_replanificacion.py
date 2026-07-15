from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from SERVICIOS.incidencias_replanificacion_rp5 import IncidenciasReplanificacionRP5


def _write(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _seed_base(tmp_path: Path):
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).date().isoformat()
    db = tmp_path / "DATOS" / "db"
    db.mkdir(parents=True, exist_ok=True)

    _write(
        db / "eventos.json",
        [
            {
                "id": "EVT-RP5-1",
                "nombre": "Servicio principal",
                "fecha": tomorrow,
                "hora_inicio": "13:30",
                "pax": 40,
                "estado": "confirmado",
                "observaciones": "Servicio piloto",
            }
        ],
    )
    _write(
        db / "menus.json",
        [
            {
                "id": "MEN-RP5-1",
                "nombre": "Menu RP5",
                "platos": [
                    {
                        "nombre": "Carrillera",
                        "ingredientes": [
                            {"articulo": "Carrillera", "unidad": "kg", "cantidad_persona": 0.3, "proveedor": "Makro"},
                            {"articulo": "Patata", "unidad": "kg", "cantidad_persona": 0.2, "proveedor": "Makro"},
                        ],
                    }
                ],
            }
        ],
    )
    _write(
        db / "stock_lotes.json",
        [
            {"id": "LOTE-CAR-1", "nombre": "Carrillera", "cantidad": 6, "unidad": "kg", "creado_en": "2026-07-15T08:00:00", "caducidad": "2026-07-16", "articulo_id": "ART-CAR"},
            {"id": "LOTE-PAT-1", "nombre": "Patata", "cantidad": 2, "unidad": "kg", "creado_en": "2026-07-15T08:00:00", "caducidad": "2026-07-18", "articulo_id": "ART-PAT"},
        ],
    )
    _write(db / "stock_inicial.json", [])
    _write(db / "articulos.json", [{"codigo": "ART-CAR", "nombre": "Carrillera"}, {"codigo": "ART-PAT", "nombre": "Patata"}])
    _write(db / "compras_pedidos.json", [])
    _write(db / "personal_turnos.json", [{"id": "PER-1", "nombre": "Ana", "turno": "manana", "horas": "08:00-16:00"}])

    plan = {
        "id": "PLAN-RP5-1",
        "version": "RP-4",
        "fecha_objetivo": tomorrow,
        "generado_en": now.isoformat(timespec="seconds"),
        "confirmado_en": now.isoformat(timespec="seconds"),
        "estado": "confirmado",
        "eventos": {"manana": [{"id": "EVT-RP5-1", "nombre": "Servicio principal", "fecha": tomorrow, "hora": "13:30", "pax": 40, "estado": "confirmado"}], "posteriores": []},
        "tareas": [
            {"id": "TAR-RP5-1", "titulo": "Base carrillera", "prioridad": 80, "estado_ejecucion": "pendiente", "recurso": "horno"},
            {"id": "TAR-RP5-2", "titulo": "Patata asada", "prioridad": 70, "estado_ejecucion": "pendiente", "recurso": "horno"},
        ],
        "descongelaciones": [],
        "compras": {"lineas": [], "total": 0, "sin_cubrir": 0},
        "recepciones": [],
        "personal": {"modo": "manual", "disponibles": [{"id": "PER-1", "nombre": "Ana"}], "revision_manual": False},
        "alergenos": {"Carrillera": ["gluten"]},
        "caducidades": [],
        "alertas": [],
        "bloqueos": [],
        "cronologia": [{"id": "CR-1", "hora": "09:00", "titulo": "Briefing", "tipo": "briefing"}],
        "solo_propuesta": True,
        "confirmacion_humana": {"tipo": "completa", "decisiones": []},
    }
    rp4_dir = tmp_path / "DATOS" / "piloto" / "rp4_preparar_manana"
    _write(rp4_dir / "confirmados.json", [plan])
    _write(rp4_dir / "propuestas.json", [plan])


def _service(tmp_path: Path) -> IncidenciasReplanificacionRP5:
    return IncidenciasReplanificacionRP5(tmp_path)


def test_rp5_registra_incidencia_y_evita_duplicados(tmp_path: Path):
    _seed_base(tmp_path)
    svc = _service(tmp_path)

    inc = svc.registrar_incidencia(
        tipo="aumento_comensales",
        gravedad="media",
        descripcion="Suben los comensales del servicio",
        origen="briefing",
        evento_id="EVT-RP5-1",
        cantidad_prevista=40,
        cantidad_real=55,
        unidad="pax",
        nuevo_valor=55,
    )
    dup = svc.registrar_incidencia(
        tipo="aumento_comensales",
        gravedad="media",
        descripcion="Suben los comensales del servicio",
        origen="briefing",
        evento_id="EVT-RP5-1",
        cantidad_prevista=40,
        cantidad_real=55,
        unidad="pax",
        nuevo_valor=55,
    )

    assert inc["estado"] == "PENDIENTE_DECISION"
    assert dup.get("duplicada") is True
    assert len(svc.listar_incidencias()) == 1


def test_rp5_impacto_y_alternativas(tmp_path: Path):
    _seed_base(tmp_path)
    svc = _service(tmp_path)

    inc = svc.registrar_incidencia(
        tipo="aumento_comensales",
        gravedad="media",
        descripcion="Aumento fuerte de servicio",
        origen="briefing",
        evento_id="EVT-RP5-1",
        cantidad_prevista=40,
        cantidad_real=58,
        unidad="pax",
        nuevo_valor=58,
    )
    analisis = svc.analizar_impacto(inc["id"])

    assert analisis["impacto_calculado"]["acciones_recalcular"]
    assert "produccion" in analisis["impacto_calculado"]["acciones_recalcular"]
    assert analisis["alternativas"]
    assert analisis["alternativas"][0]["id"]


def test_rp5_confirma_replanificacion_y_versiona(tmp_path: Path):
    _seed_base(tmp_path)
    svc = _service(tmp_path)

    inc = svc.registrar_incidencia(
        tipo="aumento_comensales",
        gravedad="media",
        descripcion="Subida de comensales con ajuste de plan",
        origen="briefing",
        evento_id="EVT-RP5-1",
        cantidad_prevista=40,
        cantidad_real=60,
        unidad="pax",
        nuevo_valor=60,
    )
    out = svc.confirmar_replanificacion(inc["id"], confirmacion="CONFIRMAR")

    version = out["version"]
    incidencia = svc.obtener_incidencia(inc["id"])

    assert out["ok"] is True
    assert version["version"] == 1
    assert version["estado"] == "confirmada"
    assert incidencia["estado"] == "RESUELTA"
    assert incidencia["plan_resultante"]["eventos"]["manana"][0]["pax"] == 60
    assert (tmp_path / "DATOS" / "piloto" / "rp5_incidencias_replan" / "versiones.json").exists()
    assert (tmp_path / "DATOS" / "piloto" / "rp5_incidencias_replan" / "propuestas.json").exists()


def test_rp5_briefing_muestra_incidencias_abiertas(tmp_path: Path):
    _seed_base(tmp_path)
    svc = _service(tmp_path)

    svc.registrar_incidencia(
        tipo="fallo_recurso",
        gravedad="alta",
        descripcion="Horno no disponible",
        origen="operativa",
        tarea_id="TAR-RP5-1",
        recurso="horno",
    )
    briefing = svc.vista_previa_briefing()

    assert briefing["solo_propuesta"] is True
    assert len(briefing["incidencias_abiertas"]) == 1
    assert briefing["incidencias_abiertas"][0]["tipo"] == "fallo_recurso"


def test_rp5_diagnostico_isolado(tmp_path: Path):
    _seed_base(tmp_path)
    svc = _service(tmp_path)

    diagnostico = svc.diagnostico()

    assert diagnostico["diagnostico"] == "OK"
    assert diagnostico["solo_propuesta"] is True
    assert diagnostico["incidencias"] == 0
