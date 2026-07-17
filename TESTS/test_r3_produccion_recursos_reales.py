from __future__ import annotations

from pathlib import Path

from SERVICIOS.configuracion_restaurante import ServicioConfiguracionRestaurante
from SERVICIOS.produccion_recursos_reales import ESTADOS_DIAGNOSTICO, ServicioProduccionRecursosReales
from SERVICIOS.recursos_restaurante import ServicioRecursosRestaurante


def _setup_base(tmp_path: Path) -> ServicioProduccionRecursosReales:
    s_r1 = ServicioConfiguracionRestaurante(tmp_path)
    cfg_r1 = s_r1.obtener_configuracion()
    s_r1.guardar_configuracion(cfg_r1)

    s_r2 = ServicioRecursosRestaurante(tmp_path)
    cfg_r2 = s_r2.obtener_configuracion()
    cfg_r2["personal"] = [
        {
            "id": "persona_ana",
            "nombre": "Ana",
            "rol": "rol_cocinero",
            "partidas": ["partida_frio", "partida_caliente"],
            "activo": True,
        },
        {
            "id": "persona_luis",
            "nombre": "Luis",
            "rol": "rol_ayudante",
            "partidas": ["partida_caliente"],
            "activo": True,
        },
    ]
    s_r2.guardar_configuracion(cfg_r2)
    return ServicioProduccionRecursosReales(tmp_path)


def _tarea(
    tid: str = "t1",
    req: dict | None = None,
    asign: dict | None = None,
    inicio: str = "08:00",
    fin: str = "09:00",
) -> dict:
    return {
        "id": tid,
        "titulo": f"Tarea {tid}",
        "hora_inicio": inicio,
        "hora_fin": fin,
        "requisitos_recursos": req or {},
        "recursos_asignados": asign or {},
    }


def _plan(tareas: list[dict]) -> dict:
    return {"id": "plan1", "tareas": tareas}


def test_01_normalizar_requisitos_claves_base(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    out = servicio.normalizar_requisitos_recursos({})
    assert set(out.keys()) == {"partida_id", "equipamiento_ids", "personas_necesarias", "turno_id", "duracion_minutos"}


def test_02_normalizar_requisitos_ids_y_duplicados(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    out = servicio.normalizar_requisitos_recursos({"equipamiento_ids": ["EQ_HORNO_RATIONAL", "eq_horno_rational", ""]})
    assert out["equipamiento_ids"] == ["eq_horno_rational"]


def test_03_normalizar_requisitos_numeros_invalidos(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    out = servicio.normalizar_requisitos_recursos({"personas_necesarias": "x", "duracion_minutos": "abc"})
    assert out["personas_necesarias"] == -1
    assert out["duracion_minutos"] == -1


def test_04_normalizar_asignados_dedup(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    out = servicio.normalizar_recursos_asignados({"persona_ids": ["PERSONA_ANA", "persona_ana"], "equipamiento_ids": ["EQ_HORNO_RATIONAL", "eq_horno_rational"]})
    assert out["persona_ids"] == ["persona_ana"]
    assert out["equipamiento_ids"] == ["eq_horno_rational"]


def test_05_validar_sin_requisitos(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    out = servicio.validar_requisitos_recursos(_tarea())
    assert out["ok"] is True
    assert out["estado"] == "sin_requisitos"


def test_06_validar_partida_inexistente(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    out = servicio.validar_requisitos_recursos(_tarea(req={"partida_id": "partida_x"}))
    assert out["ok"] is False
    assert any("Partida requerida inexistente" in p for p in out["problemas"])


def test_07_validar_partida_inactiva(tmp_path: Path):
    _setup_base(tmp_path)
    s_r1 = ServicioConfiguracionRestaurante(tmp_path)
    cfg = s_r1.obtener_configuracion()
    for p in cfg["partidas"]:
        if p["id"] == "partida_frio":
            p["activa"] = False
    s_r1.guardar_configuracion(cfg)

    servicio = ServicioProduccionRecursosReales(tmp_path)
    out = servicio.validar_requisitos_recursos(_tarea(req={"partida_id": "partida_frio"}))
    assert out["ok"] is False
    assert any("Partida inactiva" in p for p in out["problemas"])


def test_08_validar_equipamiento_inexistente(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    out = servicio.validar_requisitos_recursos(_tarea(req={"equipamiento_ids": ["eq_x"]}))
    assert out["ok"] is False
    assert any("Equipamiento inexistente" in p for p in out["problemas"])


def test_09_validar_equipamiento_inactivo(tmp_path: Path):
    _setup_base(tmp_path)
    s_r1 = ServicioConfiguracionRestaurante(tmp_path)
    cfg = s_r1.obtener_configuracion()
    for eq in cfg["equipamiento"]:
        if eq["id"] == "eq_horno_rational":
            eq["activo"] = False
    s_r1.guardar_configuracion(cfg)

    servicio = ServicioProduccionRecursosReales(tmp_path)
    out = servicio.validar_requisitos_recursos(_tarea(req={"equipamiento_ids": ["eq_horno_rational"]}))
    assert out["ok"] is False
    assert any("Equipamiento inactivo" in p for p in out["problemas"])


def test_10_validar_personas_negativas(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    out = servicio.validar_requisitos_recursos(_tarea(req={"personas_necesarias": -1}))
    assert out["ok"] is False
    assert any("personas_necesarias" in p for p in out["problemas"])


def test_11_validar_duracion_invalida(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    out = servicio.validar_requisitos_recursos(_tarea(req={"duracion_minutos": 0}))
    assert out["ok"] is False
    assert any("duracion_minutos" in p for p in out["problemas"])


def test_12_validar_turno_inexistente(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    out = servicio.validar_requisitos_recursos(_tarea(req={"turno_id": "turno_x"}))
    assert out["ok"] is False
    assert any("Turno inexistente" in p for p in out["problemas"])


def test_13_validar_turno_existente_con_aviso(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    out = servicio.validar_requisitos_recursos(_tarea(req={"turno_id": "turno_manana", "personas_necesarias": 1}))
    assert out["ok"] is True
    assert out["estado"] in {"disponible", "disponible_con_avisos"}
    assert len(out["avisos"]) >= 1


def test_14_validar_supera_capacidad_cocineros(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    out = servicio.validar_requisitos_recursos(_tarea(req={"personas_necesarias": 10}))
    assert out["ok"] is False
    assert any("cocineros_simultaneos" in p for p in out["problemas"])


def test_15_obtener_candidatos_por_partida(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    candidatos = servicio.obtener_personal_candidato(_tarea(req={"partida_id": "partida_caliente"}))
    ids = {c["id"] for c in candidatos}
    assert ids == {"persona_ana", "persona_luis"}


def test_16_obtener_candidatos_filtra_rol_inexistente(tmp_path: Path):
    _setup_base(tmp_path)
    s_r2 = ServicioRecursosRestaurante(tmp_path)
    cfg = s_r2.obtener_configuracion()
    cfg["personal"].append(
        {
            "id": "persona_sinrol",
            "nombre": "Sin Rol",
            "rol": "rol_no_existe",
            "partidas": ["partida_caliente"],
            "activo": True,
        }
    )
    cfg["capacidades"]["cocineros_simultaneos"] = 4
    s_r2.ruta_configuracion.write_text(__import__("json").dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

    servicio = ServicioProduccionRecursosReales(tmp_path)
    candidatos = servicio.obtener_personal_candidato(_tarea(req={"partida_id": "partida_caliente"}))
    ids = {c["id"] for c in candidatos}
    assert "persona_sinrol" not in ids


def test_17_diagnosticar_tarea_sin_requisitos(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    out = servicio.diagnosticar_recursos_tarea(_tarea())
    assert out["estado"] == "sin_requisitos"
    assert out["bloqueante"] is False


def test_18_diagnosticar_tarea_personal_insuficiente(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    req = {"partida_id": "partida_caliente", "personas_necesarias": 3}
    out = servicio.diagnosticar_recursos_tarea(_tarea(req=req))
    assert out["bloqueante"] is True
    assert any("Personal insuficiente" in p for p in out["problemas"])


def test_19_diagnosticar_tarea_equipamiento_disponible(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    req = {"equipamiento_ids": ["eq_horno_rational"], "personas_necesarias": 0}
    out = servicio.diagnosticar_recursos_tarea(_tarea(req=req))
    assert "eq_horno_rational" in out["equipamiento_disponible"]


def test_20_validar_asignacion_persona_duplicada(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    req = {"partida_id": "partida_caliente", "personas_necesarias": 1}
    tarea = _tarea(req=req)
    out = servicio.validar_asignacion_recursos(_plan([tarea]), tarea, {"persona_ids": ["persona_ana", "persona_ana"]})
    assert out["ok"] is False
    assert any("misma persona" in p for p in out["problemas"])


def test_21_validar_asignacion_persona_incompatible(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    req = {"partida_id": "partida_postres", "personas_necesarias": 1}
    tarea = _tarea(req=req)
    out = servicio.validar_asignacion_recursos(_plan([tarea]), tarea, {"persona_ids": ["persona_ana"]})
    assert out["ok"] is False
    assert any("no compatible" in p for p in out["problemas"])


def test_22_validar_asignacion_equipamiento_inactivo(tmp_path: Path):
    _setup_base(tmp_path)
    s_r1 = ServicioConfiguracionRestaurante(tmp_path)
    cfg = s_r1.obtener_configuracion()
    for eq in cfg["equipamiento"]:
        if eq["id"] == "eq_horno_rational":
            eq["activo"] = False
    s_r1.guardar_configuracion(cfg)

    servicio = ServicioProduccionRecursosReales(tmp_path)
    req = {"equipamiento_ids": ["eq_horno_rational"]}
    tarea = _tarea(req=req)
    out = servicio.validar_asignacion_recursos(_plan([tarea]), tarea, {"equipamiento_ids": ["eq_horno_rational"]})
    assert out["ok"] is False
    assert any("inactivo" in p for p in out["problemas"])


def test_23_validar_asignacion_exceso_sin_confirmacion(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    req = {"partida_id": "partida_caliente", "personas_necesarias": 1}
    tarea = _tarea(req=req)
    out = servicio.validar_asignacion_recursos(
        _plan([tarea]),
        tarea,
        {"persona_ids": ["persona_ana", "persona_luis"]},
        confirmar_exceso_personas=False,
    )
    assert out["ok"] is False
    assert any("supera personas_necesarias" in p for p in out["problemas"])


def test_24_validar_asignacion_exceso_con_confirmacion(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    req = {"partida_id": "partida_caliente", "personas_necesarias": 1}
    tarea = _tarea(req=req)
    out = servicio.validar_asignacion_recursos(
        _plan([tarea]),
        tarea,
        {"persona_ids": ["persona_ana", "persona_luis"]},
        confirmar_exceso_personas=True,
    )
    assert out["ok"] is True


def test_25_conflicto_equipamiento_solapado(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    a = _tarea("t1", req={"equipamiento_ids": ["eq_horno_rational"], "duracion_minutos": 60}, inicio="08:00", fin="09:00")
    b = _tarea("t2", req={"equipamiento_ids": ["eq_horno_rational"], "duracion_minutos": 60}, inicio="08:30", fin="09:30")
    out = servicio.detectar_conflictos_recursos(_plan([a, b]))
    assert out["bloqueante"] is True
    assert any(c.get("tipo") == "equipamiento" for c in out["conflictos"])


def test_26_conflicto_personal_solapado(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    a = _tarea("t1", req={"personas_necesarias": 1}, asign={"persona_ids": ["persona_ana"]}, inicio="08:00", fin="09:00")
    b = _tarea("t2", req={"personas_necesarias": 1}, asign={"persona_ids": ["persona_ana"]}, inicio="08:20", fin="09:10")
    out = servicio.detectar_conflictos_recursos(_plan([a, b]))
    assert any(c.get("tipo") == "personal" for c in out["conflictos"])


def test_27_sin_conflicto_si_no_hay_solape(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    a = _tarea("t1", req={"equipamiento_ids": ["eq_horno_rational"]}, inicio="08:00", fin="09:00")
    b = _tarea("t2", req={"equipamiento_ids": ["eq_horno_rational"]}, inicio="09:00", fin="10:00")
    out = servicio.detectar_conflictos_recursos(_plan([a, b]))
    assert out["bloqueante"] is False


def test_28_conflicto_capacidad_elaboraciones(tmp_path: Path):
    _setup_base(tmp_path)
    s_r2 = ServicioRecursosRestaurante(tmp_path)
    cfg = s_r2.obtener_configuracion()
    cfg["capacidades"]["elaboraciones_simultaneas"] = 1
    s_r2.guardar_configuracion(cfg)

    servicio = ServicioProduccionRecursosReales(tmp_path)
    a = _tarea("t1", req={"personas_necesarias": 1}, inicio="08:00", fin="09:00")
    b = _tarea("t2", req={"personas_necesarias": 1}, inicio="08:10", fin="09:10")
    out = servicio.detectar_conflictos_recursos(_plan([a, b]))
    assert any(c.get("tipo") == "capacidad_elaboraciones" for c in out["conflictos"])


def test_29_conflicto_capacidad_personas(tmp_path: Path):
    _setup_base(tmp_path)
    s_r2 = ServicioRecursosRestaurante(tmp_path)
    cfg = s_r2.obtener_configuracion()
    cfg["capacidades"]["cocineros_simultaneos"] = 1
    s_r2.guardar_configuracion(cfg)

    servicio = ServicioProduccionRecursosReales(tmp_path)
    a = _tarea("t1", req={"personas_necesarias": 1}, inicio="08:00", fin="09:00")
    b = _tarea("t2", req={"personas_necesarias": 1}, inicio="08:10", fin="09:10")
    out = servicio.detectar_conflictos_recursos(_plan([a, b]))
    assert any(c.get("tipo") == "capacidad_personas" for c in out["conflictos"])


def test_30_aviso_por_temporal_incompleto(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    a = _tarea("t1", req={"personas_necesarias": 1}, inicio="", fin="")
    out = servicio.detectar_conflictos_recursos(_plan([a]))
    assert len(out["avisos"]) >= 1


def test_31_diagnosticar_plan_resumen_basico(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    a = _tarea("t1")
    b = _tarea("t2", req={"partida_id": "partida_caliente", "personas_necesarias": 1})
    out = servicio.diagnosticar_recursos_plan(_plan([a, b]))
    assert out["resumen"]["tareas_totales"] == 2
    assert out["resumen"]["sin_requisitos"] >= 1


def test_32_diagnosticar_plan_inyecta_conflictos_en_tarea(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    a = _tarea("t1", req={"equipamiento_ids": ["eq_horno_rational"], "duracion_minutos": 60}, inicio="08:00", fin="09:00")
    b = _tarea("t2", req={"equipamiento_ids": ["eq_horno_rational"], "duracion_minutos": 60}, inicio="08:10", fin="09:10")
    out = servicio.diagnosticar_recursos_plan(_plan([a, b]))
    assert out["resumen"]["bloqueadas"] >= 1
    assert len(out["problemas_bloqueantes"]) >= 1


def test_33_diagnosticar_plan_avisos_unicos(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    a = _tarea("t1", req={"turno_id": "turno_manana", "personas_necesarias": 1}, inicio="", fin="")
    out = servicio.diagnosticar_recursos_plan(_plan([a]))
    assert len(out["avisos"]) == len(set(out["avisos"]))


def test_34_detectar_conflictos_plan_vacio(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    out = servicio.detectar_conflictos_recursos(_plan([]))
    assert out["bloqueante"] is False
    assert out["conflictos"] == []


def test_35_estados_diagnostico_devueltos_son_validos(tmp_path: Path):
    servicio = _setup_base(tmp_path)
    casos = [
        _tarea("a"),
        _tarea("b", req={"partida_id": "partida_caliente", "personas_necesarias": 1}),
        _tarea("c", req={"partida_id": "partida_x"}),
    ]
    out = servicio.diagnosticar_recursos_plan(_plan(casos))
    for diag in out["diagnostico_tareas"].values():
        assert diag["estado"] in ESTADOS_DIAGNOSTICO
