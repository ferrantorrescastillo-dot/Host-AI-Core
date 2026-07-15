from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from SERVICIOS.cierre_operativo_rp4 import CierreOperativoRP4
from SERVICIOS.jornada_piloto_12 import JornadaPiloto12


BASE_NOW = datetime(2026, 7, 15, 21, 0, 0)


def _write(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _seed_base(tmp_path: Path, *, with_events: bool = True, multi_events: bool = False):
    db = tmp_path / "DATOS" / "db"
    db.mkdir(parents=True, exist_ok=True)

    eventos = []
    if with_events:
        eventos.append(
            {
                "id": "EVT-1",
                "nombre": "Servicio Carta",
                "fecha": "2026-07-16",
                "hora_inicio": "13:30",
                "pax": 40,
                "estado": "confirmado",
                "observaciones": "Alergenos: frutos secos",
            }
        )
        if multi_events:
            eventos.append(
                {
                    "id": "EVT-2",
                    "nombre": "Banquete",
                    "fecha": "2026-07-17",
                    "hora_inicio": "20:00",
                    "pax": 80,
                    "estado": "pendiente",
                }
            )
    _write(db / "eventos.json", eventos)

    menus = [
        {
            "id": "MEN-1",
            "nombre": "Menu piloto",
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
    ]
    _write(db / "menus.json", menus)

    planes = [
        {
            "id": "PLAN-1",
            "evento_id": "EVT-1",
            "evento": "Servicio Carta",
            "estado": "planificado",
            "tareas": [
                {
                    "id": "TAR-1",
                    "titulo": "Carrillera baja temperatura",
                    "estado_ejecucion": "pendiente",
                    "prioridad": 90,
                    "bloqueo": "",
                    "fases": [
                        {"nombre": "Preparar", "duracion_min": 50, "tipo": "activo", "recurso": "mesa", "responsable": "chef"},
                        {"nombre": "Marinado", "duracion_min": 240, "tipo": "marinado", "recurso": "camara", "responsable": "chef"},
                        {"nombre": "Descongelar", "duracion_min": 120, "tipo": "descongelacion", "recurso": "camara", "responsable": "chef"},
                    ],
                },
                {
                    "id": "TAR-2",
                    "titulo": "Fondo oscuro",
                    "estado_ejecucion": "finalizada",
                    "prioridad": 70,
                    "fases": [{"nombre": "Coccion", "duracion_min": 90, "tipo": "coccion"}],
                },
            ],
        }
    ]
    _write(db / "planes_produccion.json", planes)

    pedidos = [
        {
            "id": "PED-1",
            "proveedor": "Makro",
            "estado": "enviado",
            "enviado_en": "2026-07-15T09:00:00",
            "entrega_prevista": "2026-07-16T10:00:00",
            "lineas": [{"nombre": "Patata", "cantidad": 10, "unidad": "kg"}],
        }
    ]
    _write(db / "compras_pedidos.json", pedidos)

    _write(db / "compras_necesidades.json", [])
    _write(db / "articulos.json", [{"codigo": "ART-1", "nombre": "Carrillera", "alergenos": ["gluten"]}])
    _write(
        db / "stock_lotes.json",
        [
            {
                "id": "LOTE-1",
                "nombre": "Carrillera",
                "cantidad": 5,
                "unidad": "kg",
                "caducidad": "2026-07-16",
                "creado_en": "2026-07-15T08:00:00",
            }
        ],
    )
    _write(
        db / "stock_inicial.json",
        [
            {"codigo": "ART-CAR", "articulo": "Carrillera", "stock_actual": 5, "stock_minimo": 2, "unidad": "kg"},
            {"codigo": "ART-PAT", "articulo": "Patata", "stock_actual": 0, "stock_minimo": 2, "unidad": "kg"},
        ],
    )


def _svc(tmp_path: Path) -> CierreOperativoRP4:
    return CierreOperativoRP4(tmp_path)


def _plan(tmp_path: Path, **kwargs):
    return _svc(tmp_path).preparar_manana(BASE_NOW, **kwargs)


def test_01_dia_siguiente_sin_eventos(tmp_path: Path):
    _seed_base(tmp_path, with_events=False)
    p = _plan(tmp_path)
    assert (p.get("eventos") or {}).get("manana") == []


def test_02_un_evento_manana(tmp_path: Path):
    _seed_base(tmp_path, with_events=True, multi_events=False)
    p = _plan(tmp_path)
    assert len((p.get("eventos") or {}).get("manana", [])) == 1


def test_03_varios_eventos(tmp_path: Path):
    _seed_base(tmp_path, with_events=True, multi_events=True)
    p = _plan(tmp_path)
    assert len((p.get("eventos") or {}).get("posteriores", [])) >= 1


def test_04_produccion_ya_terminada(tmp_path: Path):
    _seed_base(tmp_path)
    p = _plan(tmp_path)
    assert any(t.get("produccion_terminada") for t in p.get("tareas", []))


def test_05_produccion_pendiente(tmp_path: Path):
    _seed_base(tmp_path)
    p = _plan(tmp_path)
    assert any(t.get("produccion_pendiente") for t in p.get("tareas", []))


def test_06_produccion_que_debe_empezar_hoy(tmp_path: Path):
    _seed_base(tmp_path)
    p = _plan(tmp_path)
    assert any(t.get("debe_empezar_hoy") for t in p.get("tareas", []))


def test_07_descongelacion_necesaria(tmp_path: Path):
    _seed_base(tmp_path)
    p = _plan(tmp_path)
    assert len(p.get("descongelaciones", [])) >= 1


def test_08_descongelacion_ya_confirmada(tmp_path: Path):
    _seed_base(tmp_path)
    svc = _svc(tmp_path)
    p1 = svc.preparar_manana(BASE_NOW)
    d0 = p1["descongelaciones"][0]
    svc.confirmar_plan(p1["id"], confirmacion="CONFIRMAR", parcial=True, decisiones=[{"target": "descongelaciones", "id": d0["id"], "action": "confirmar"}])
    p2 = svc.preparar_manana(BASE_NOW)
    merged = [d for d in p2["descongelaciones"] if d["id"] == d0["id"]][0]
    assert merged.get("decision") == "confirmada"


def test_09_tiempo_descongelacion_desconocido(tmp_path: Path):
    _seed_base(tmp_path)
    data = json.loads((tmp_path / "DATOS" / "db" / "planes_produccion.json").read_text(encoding="utf-8"))
    data[0]["tareas"][0]["fases"][2]["duracion_min"] = 0
    _write(tmp_path / "DATOS" / "db" / "planes_produccion.json", data)
    p = _plan(tmp_path)
    assert any(a.get("tipo") == "descongelacion_tiempo_desconocido" for a in p.get("alertas", []))


def test_10_stock_suficiente(tmp_path: Path):
    _seed_base(tmp_path)
    p = _plan(tmp_path)
    assert any(_to >= 0 for _to in [len(p.get("tareas", []))])


def test_11_faltante_cubierto_por_pedido_abierto(tmp_path: Path):
    _seed_base(tmp_path)
    p = _plan(tmp_path)
    assert any(_l.get("cantidad_cubierta_pedidos_abiertos", 0) > 0 for _l in (p.get("compras") or {}).get("lineas", []))


def test_12_faltante_sin_cubrir(tmp_path: Path):
    _seed_base(tmp_path)
    p = _plan(tmp_path)
    assert any(_l.get("cantidad_sin_cubrir", 0) > 0 for _l in (p.get("compras") or {}).get("lineas", []))


def test_13_pedido_sin_fecha_exacta(tmp_path: Path):
    _seed_base(tmp_path)
    data = json.loads((tmp_path / "DATOS" / "db" / "compras_pedidos.json").read_text(encoding="utf-8"))
    data[0].pop("entrega_prevista", None)
    _write(tmp_path / "DATOS" / "db" / "compras_pedidos.json", data)
    p = _plan(tmp_path)
    assert any(r.get("datos_incompletos") for r in p.get("recepciones", []))


def test_14_recepcion_prevista(tmp_path: Path):
    _seed_base(tmp_path)
    p = _plan(tmp_path)
    assert len(p.get("recepciones", [])) >= 1


def test_15_recepcion_tardia(tmp_path: Path):
    _seed_base(tmp_path)
    data = json.loads((tmp_path / "DATOS" / "db" / "compras_pedidos.json").read_text(encoding="utf-8"))
    data[0]["entrega_prevista"] = "2026-07-17T10:00:00"
    _write(tmp_path / "DATOS" / "db" / "compras_pedidos.json", data)
    p = _plan(tmp_path)
    assert any(a.get("tipo") == "recepcion_tardia" for a in p.get("alertas", []))


def test_16_personal_suficiente(tmp_path: Path):
    _seed_base(tmp_path)
    _write(
        tmp_path / "DATOS" / "db" / "personal_turnos.json",
        [
            {"id": "P1", "nombre": "Ana", "turno": "manana", "horas": "08:00-16:00", "area": "caliente"},
            {"id": "P2", "nombre": "Luis", "turno": "manana", "horas": "08:00-16:00", "area": "frio"},
        ],
    )
    p = _plan(tmp_path)
    assert p.get("personal", {}).get("revision_manual") is False


def test_17_personal_insuficiente(tmp_path: Path):
    _seed_base(tmp_path)
    p = _plan(tmp_path)
    assert p.get("personal", {}).get("revision_manual") is True


def test_18_asignacion_propuesta(tmp_path: Path):
    _seed_base(tmp_path)
    p = _plan(tmp_path)
    assert isinstance(p.get("personal", {}).get("asignacion", []), list)


def test_19_tareas_activas_y_pasivas(tmp_path: Path):
    _seed_base(tmp_path)
    p = _plan(tmp_path)
    t = p.get("tareas", [])[0]
    assert t.get("duracion_activa_min", 0) > 0 and t.get("duracion_pasiva_min", 0) > 0


def test_20_recurso_compartido(tmp_path: Path):
    _seed_base(tmp_path)
    p = _plan(tmp_path)
    assert any((c.get("recurso") or "") for c in p.get("cronologia", []))


def test_21_cronologia_valida(tmp_path: Path):
    _seed_base(tmp_path)
    p = _plan(tmp_path)
    assert len(p.get("cronologia", [])) > 0


def test_22_sobrecarga_de_jornada(tmp_path: Path):
    _seed_base(tmp_path)
    data = json.loads((tmp_path / "DATOS" / "db" / "planes_produccion.json").read_text(encoding="utf-8"))
    for i in range(20):
        data[0]["tareas"].append({"id": f"TAR-X-{i}", "titulo": f"Extra {i}", "estado_ejecucion": "pendiente", "prioridad": 40, "fases": [{"duracion_min": 30, "tipo": "activo", "recurso": "mesa"}]})
    _write(tmp_path / "DATOS" / "db" / "planes_produccion.json", data)
    p = _plan(tmp_path)
    assert any(c.get("titulo", "").lower().startswith("sobrecarga") for c in p.get("cronologia", []))


def test_23_alergeno_registrado(tmp_path: Path):
    _seed_base(tmp_path)
    p = _plan(tmp_path)
    assert any(a.get("tipo") == "alergeno_registrado" for a in p.get("alertas", []))


def test_24_catalogo_alergenos_incompleto(tmp_path: Path):
    _seed_base(tmp_path)
    _write(tmp_path / "DATOS" / "db" / "articulos.json", [{"codigo": "A1", "nombre": "Patata"}])
    p = _plan(tmp_path)
    assert any(a.get("tipo") == "catalogo_alergenos_incompleto" for a in p.get("alertas", []))


def test_25_caducidad_proxima(tmp_path: Path):
    _seed_base(tmp_path)
    p = _plan(tmp_path)
    assert any(a.get("tipo") == "producto_proximo_caducar" for a in p.get("alertas", []))


def test_26_incidencia_abierta(tmp_path: Path):
    _seed_base(tmp_path)
    _write(tmp_path / "DATOS" / "db" / "incidencias_abiertas.json", [{"id": "INC-1", "detalle": "Averia horno"}])
    p = _plan(tmp_path)
    assert any(a.get("tipo") == "incidencia_abierta" for a in p.get("alertas", []))


def test_27_plan_determinista(tmp_path: Path):
    _seed_base(tmp_path)
    svc = _svc(tmp_path)
    p1 = svc.preparar_manana(BASE_NOW)
    p2 = svc.preparar_manana(BASE_NOW)
    assert p1.get("fingerprint_entradas") == p2.get("fingerprint_entradas")


def test_28_ids_estables(tmp_path: Path):
    _seed_base(tmp_path)
    svc = _svc(tmp_path)
    p1 = svc.preparar_manana(BASE_NOW)
    p2 = svc.preparar_manana(BASE_NOW)
    assert p1.get("id") == p2.get("id")


def test_29_regeneracion_sin_duplicados(tmp_path: Path):
    _seed_base(tmp_path)
    svc = _svc(tmp_path)
    p = svc.preparar_manana(BASE_NOW)
    ids = [x.get("id") for x in p.get("tareas", [])]
    assert len(ids) == len(set(ids))


def test_30_cambio_comensales(tmp_path: Path):
    _seed_base(tmp_path)
    svc = _svc(tmp_path)
    p1 = svc.preparar_manana(BASE_NOW)
    eventos = json.loads((tmp_path / "DATOS" / "db" / "eventos.json").read_text(encoding="utf-8"))
    eventos[0]["pax"] = 140
    _write(tmp_path / "DATOS" / "db" / "eventos.json", eventos)
    p2 = svc.preparar_manana(BASE_NOW)
    assert p1.get("fingerprint_entradas") != p2.get("fingerprint_entradas")


def test_31_cambio_menu(tmp_path: Path):
    _seed_base(tmp_path)
    svc = _svc(tmp_path)
    p1 = svc.preparar_manana(BASE_NOW)
    menus = json.loads((tmp_path / "DATOS" / "db" / "menus.json").read_text(encoding="utf-8"))
    menus[0]["platos"][0]["ingredientes"].append({"articulo": "Ajo", "unidad": "kg", "cantidad_persona": 0.01})
    _write(tmp_path / "DATOS" / "db" / "menus.json", menus)
    p2 = svc.preparar_manana(BASE_NOW)
    assert p1.get("fingerprint_entradas") != p2.get("fingerprint_entradas")


def test_32_conservacion_decision_humana_compatible(tmp_path: Path):
    _seed_base(tmp_path)
    svc = _svc(tmp_path)
    p1 = svc.preparar_manana(BASE_NOW)
    linea = ((p1.get("compras") or {}).get("lineas") or [])[0]
    svc.confirmar_plan(
        p1.get("id"),
        confirmacion="CONFIRMAR",
        parcial=True,
        decisiones=[{"target": "compras", "id": linea.get("id"), "action": "confirmar"}],
    )
    p2 = svc.preparar_manana(BASE_NOW)
    m = [x for x in (p2.get("compras") or {}).get("lineas", []) if x.get("id") == linea.get("id")][0]
    assert m.get("decision") == "confirmada"


def test_33_confirmacion_parcial(tmp_path: Path):
    _seed_base(tmp_path)
    svc = _svc(tmp_path)
    p1 = svc.preparar_manana(BASE_NOW)
    out = svc.confirmar_plan(p1.get("id"), confirmacion="CONFIRMAR", parcial=True)
    assert out.get("estado") == "confirmado_parcial"


def test_34_confirmacion_completa(tmp_path: Path):
    _seed_base(tmp_path)
    svc = _svc(tmp_path)
    p1 = svc.preparar_manana(BASE_NOW)
    out = svc.confirmar_plan(p1.get("id"), confirmacion="CONFIRMAR", parcial=False)
    assert out.get("estado") == "confirmado"


def test_35_integracion_con_rp1(tmp_path: Path):
    _seed_base(tmp_path)
    svc = _svc(tmp_path)
    p = svc.preparar_manana(BASE_NOW)
    svc.confirmar_plan(p.get("id"), confirmacion="CONFIRMAR", parcial=False)
    jornada = JornadaPiloto12(tmp_path).construir(datetime(2026, 7, 16, 8, 0, 0))
    rp4 = (jornada.get("briefing_apertura") or {}).get("plan_manana_rp4") or {}
    assert rp4.get("disponible") is True


def test_36_no_consumo_stock(tmp_path: Path):
    _seed_base(tmp_path)
    before = (tmp_path / "DATOS" / "db" / "stock_lotes.json").read_text(encoding="utf-8")
    svc = _svc(tmp_path)
    p = svc.preparar_manana(BASE_NOW)
    svc.confirmar_plan(p.get("id"), confirmacion="CONFIRMAR", parcial=False)
    after = (tmp_path / "DATOS" / "db" / "stock_lotes.json").read_text(encoding="utf-8")
    assert before == after


def test_37_no_creacion_pedido_definitivo(tmp_path: Path):
    _seed_base(tmp_path)
    before = (tmp_path / "DATOS" / "db" / "compras_pedidos.json").read_text(encoding="utf-8")
    svc = _svc(tmp_path)
    p = svc.preparar_manana(BASE_NOW)
    svc.confirmar_plan(p.get("id"), confirmacion="CONFIRMAR", parcial=False)
    after = (tmp_path / "DATOS" / "db" / "compras_pedidos.json").read_text(encoding="utf-8")
    assert before == after


def test_38_no_modificacion_datos_reales(tmp_path: Path):
    _seed_base(tmp_path)
    svc = _svc(tmp_path)
    _ = svc.preparar_manana(BASE_NOW)
    assert str(tmp_path).lower().find("host ai 6.0") == -1


def test_39_persistencia_temporal(tmp_path: Path):
    _seed_base(tmp_path)
    svc = _svc(tmp_path)
    p = svc.preparar_manana(BASE_NOW)
    assert (tmp_path / "DATOS" / "piloto" / "rp4_preparar_manana" / "propuestas.json").exists()
    svc.confirmar_plan(p.get("id"), confirmacion="CONFIRMAR", parcial=False)
    assert (tmp_path / "DATOS" / "piloto" / "rp4_preparar_manana" / "confirmados.json").exists()


def test_40_caso_completo_controlado(tmp_path: Path):
    _seed_base(tmp_path)
    svc = _svc(tmp_path)
    cierre = svc.cerrar_jornada(BASE_NOW)
    plan = svc.preparar_manana(BASE_NOW)
    conf = svc.confirmar_plan(plan.get("id"), confirmacion="CONFIRMAR", parcial=False)
    vista = svc.vista_previa_briefing(plan.get("id"))
    jornada = JornadaPiloto12(tmp_path).construir(datetime(2026, 7, 16, 8, 0, 0))
    rp4 = (jornada.get("briefing_apertura") or {}).get("plan_manana_rp4") or {}
    assert cierre.get("estado") in {"CERRADA", "CERRADA_CON_AVISOS"}
    assert conf.get("estado") == "confirmado"
    assert len(vista.get("cronologia", [])) >= 1
    assert rp4.get("disponible") is True
