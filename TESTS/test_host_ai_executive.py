from __future__ import annotations

import json
from pathlib import Path

from SERVICIOS.host_ai_executive import (
    EXEC_INTENCION_BLOQUEO_PRODUCCION,
    EXEC_INTENCION_DESBLOQUEO,
    EXEC_INTENCION_IMPACTO_COMPRAS,
    EXEC_INTENCION_IMPACTO_PRODUCCION,
    EXEC_INTENCION_MOTIVO_PRIORIDAD,
    EXEC_INTENCION_PLAN_DIA,
    EXEC_INTENCION_PLAN_OPERATIVO,
    EXEC_INTENCION_RESTAURANTE,
    HostAIExecutive,
    EXEC_INTENCION_PENDIENTES,
    EXEC_INTENCION_PRIORIDAD,
    EXEC_INTENCION_RECOMENDACIONES,
    explicar_impacto_operativo,
    formatear_respuesta_executive_conversacional,
    presentar_accion_ejecutiva,
)


DATOS_EVENTO = {
    "tipo": "boda",
    "personas": 180,
    "fecha": "sabado",
    "hora_servicio": "15:00",
    "menu": "menu boda",
    "lugar": "Mas Boronat",
    "restricciones": "sin restricciones",
    "objetivo": "flujo completo",
}


def test_host_ai_executive_coordina_y_reporta_en_modo_seguro(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    resultado = servicio.analizar_evento(DATOS_EVENTO)

    assert resultado.get("ok") is True
    assert resultado.get("estado") == "analisis_completo"
    assert isinstance(resultado.get("workflows_priorizados"), list)
    assert isinstance(resultado.get("workflows_ejecutados"), list)
    assert isinstance(resultado.get("pendientes"), list)
    assert isinstance(resultado.get("riesgos"), list)
    assert isinstance(resultado.get("resumen_ejecutivo"), str)
    assert isinstance(resultado.get("estado_general"), str)
    assert isinstance(resultado.get("prioridad_inmediata"), dict)
    assert isinstance(resultado.get("pendientes_operativos"), list)
    assert isinstance(resultado.get("riesgos_operativos"), list)
    assert isinstance(resultado.get("recomendaciones_operativas"), list)
    assert isinstance(resultado.get("resumen_ejecutivo_lineas"), list)
    assert resultado.get("datos_reales_modificados") is False

    prioridad = dict(resultado.get("prioridad_inmediata") or {})
    assert str(prioridad.get("titulo") or "").strip()
    assert str(prioridad.get("justificacion") or "").strip()

    pendientes_operativos = list(resultado.get("pendientes_operativos") or [])
    assert pendientes_operativos
    assert all(any(ch.isalpha() for ch in str(p)) for p in pendientes_operativos)

    recomendaciones = list(resultado.get("recomendaciones_operativas") or [])
    assert recomendaciones
    assert any("menú" in str(r).lower() or "menu" in str(r).lower() for r in recomendaciones)

    lineas = [str(x) for x in list(resultado.get("resumen_ejecutivo_lineas") or [])]
    assert 1 <= len(lineas) <= 5
    assert any("modo seguro" in l.lower() for l in lineas)


def test_host_ai_executive_no_ejecuta_pasos_criticos_y_mantiene_continuidad(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    resultado = servicio.analizar_evento(DATOS_EVENTO)

    ejecutados = list(resultado.get("workflows_ejecutados") or [])
    pendientes = list(resultado.get("pendientes") or [])
    continuidad = dict(resultado.get("continuidad_conversacional") or {})

    assert all(bool(item.get("modifica_datos")) is False for item in ejecutados)
    codigos_pendientes = {str(item.get("codigo") or "") for item in pendientes}
    assert "EVENTO_CREAR" in codigos_pendientes
    assert "MENU_ASOCIAR" in codigos_pendientes
    assert continuidad.get("flujo_pendiente_confirmacion") is True
    assert continuidad.get("activo") is True


def test_host_ai_executive_v2_es_determinista_en_interpretacion(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    r1 = servicio.analizar_evento(DATOS_EVENTO)
    r2 = servicio.analizar_evento(DATOS_EVENTO)

    assert r1.get("estado_general") == r2.get("estado_general")
    assert r1.get("prioridad_inmediata") == r2.get("prioridad_inmediata")
    assert r1.get("pendientes_operativos") == r2.get("pendientes_operativos")
    assert r1.get("riesgos_operativos") == r2.get("riesgos_operativos")
    assert r1.get("recomendaciones_operativas") == r2.get("recomendaciones_operativas")
    assert r1.get("resumen_ejecutivo") == r2.get("resumen_ejecutivo")
    assert r1.get("datos_reales_modificados") is False
    assert r2.get("datos_reales_modificados") is False


def test_host_ai_executive_no_muestra_confirmar_evento_si_ya_existe(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    datos = dict(DATOS_EVENTO)
    datos["id"] = "EVT-EXISTENTE-1"

    resultado = servicio.analizar_evento(datos)
    pendientes_operativos = [str(x) for x in list(resultado.get("pendientes_operativos") or [])]

    assert all("crear" not in p.lower() or "evento" not in p.lower() for p in pendientes_operativos)


def test_host_ai_executive_mantiene_pendiente_evento_si_no_existe(tmp_path, monkeypatch) -> None:
    servicio = HostAIExecutive(tmp_path)

    flujo_minimo = {
        "pasos": [
            {
                "codigo": "EVENTO_CREAR",
                "nombre": "Crear o localizar evento",
                "requiere_confirmacion": True,
                "modifica_datos": True,
                "estado": "pendiente",
            }
        ]
    }

    monkeypatch.setattr(servicio.orquestador_flujo, "iniciar_flujo_operativo", lambda _d: {"ok": True, "flujo": flujo_minimo})
    monkeypatch.setattr(
        servicio.orquestador_flujo,
        "ejecutar_flujo_seguro",
        lambda _f, confirmar=False: {
            "flujo": flujo_minimo,
            "resultados": [],
            "pendientes_confirmacion": [{"codigo": "EVENTO_CREAR"}],
        },
    )

    resultado = servicio.analizar_evento(DATOS_EVENTO)
    pendientes_operativos = [str(x) for x in list(resultado.get("pendientes_operativos") or [])]

    assert any(("creacion" in p.lower() or "creación" in p.lower()) and "evento" in p.lower() for p in pendientes_operativos)


def test_host_ai_executive_etiquetas_naturales_en_bloques(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    datos = dict(DATOS_EVENTO)
    datos["id"] = "EVT-NATURAL-1"
    resultado = servicio.analizar_evento(datos)

    pendientes_txt = formatear_respuesta_executive_conversacional(resultado, EXEC_INTENCION_PENDIENTES)
    prioridad_txt = formatear_respuesta_executive_conversacional(resultado, EXEC_INTENCION_PRIORIDAD)
    recomendaciones_txt = formatear_respuesta_executive_conversacional(resultado, EXEC_INTENCION_RECOMENDACIONES)

    assert "Completar el menú del evento" in pendientes_txt or "Asignar los platos y pases" in pendientes_txt
    prioridad_txt_norm = prioridad_txt.lower()
    assert "generar la planificación de cocina" in prioridad_txt_norm or "revisar la propuesta de compras del evento" in prioridad_txt_norm or "completar el menú del evento" in prioridad_txt_norm
    assert "Revisar la propuesta de compras del evento" in recomendaciones_txt or "Comprobar que hay stock suficiente" in recomendaciones_txt
    assert "Cuando completes completar menú" not in pendientes_txt


def test_host_ai_executive_riesgo_concreto_menu_incompleto(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    datos = dict(DATOS_EVENTO)
    datos["id"] = "EVT-RIESGO-1"
    resultado = servicio.analizar_evento(datos)

    riesgos = [str(x) for x in list(resultado.get("riesgos_operativos") or [])]
    assert any("menú no esté completo" in r or "menu no este completo" in r.lower() for r in riesgos)


def test_presentar_accion_ejecutiva_mapeo_base() -> None:
    assert presentar_accion_ejecutiva("Completar Menú") == "Completar el menú del evento"
    assert presentar_accion_ejecutiva("Preparar Producción") == "Generar la planificación de cocina"
    assert presentar_accion_ejecutiva("Revisar Compras") == "Revisar la propuesta de compras del evento"


class _EventoFake:
    def __init__(self, *, evento_id: str, nombre: str, fecha: str, estado: str = "pendiente", pax: int = 0):
        self.id = evento_id
        self.nombre = nombre
        self.fecha = fecha
        self.estado = estado
        self.pax = pax


class _EventosFake:
    def __init__(self, eventos: list[_EventoFake], avisos_por_evento: dict[str, list[str]]):
        self._eventos = eventos
        self._avisos = avisos_por_evento

    def listar_eventos(self):
        return list(self._eventos)

    def resumen_ejecutivo(self, evento_id: str):
        return {"avisos": list(self._avisos.get(evento_id, []))}


class _ComprasFake:
    def __init__(self, propuestas: list[dict]):
        self._propuestas = propuestas

    def listar_propuestas_compra(self, solo_pendientes: bool = True):
        if not solo_pendientes:
            return list(self._propuestas)
        return [p for p in self._propuestas if str(p.get("estado") or "pendiente").lower() in {"pendiente", "preparada", "propuesta"}]


class _CoreFake:
    def __init__(self, eventos: list[_EventoFake], avisos_por_evento: dict[str, list[str]], propuestas: list[dict]):
        self.eventos = _EventosFake(eventos, avisos_por_evento)
        self.compras = _ComprasFake(propuestas)


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_executive_diario_restaurante_sin_eventos(tmp_path) -> None:
    _write_json(tmp_path / "DATOS" / "db" / "planes_produccion.json", [])
    _write_json(tmp_path / "DATOS" / "db" / "compras_propuestas.json", [])
    _write_json(tmp_path / "DATOS" / "db" / "stock_inicial.json", [])
    core = _CoreFake([], {}, [])

    resultado = HostAIExecutive(tmp_path).analizar_restaurante(core=core)
    resumen = dict(resultado.get("resumen_restaurante") or {})

    assert resultado.get("ok") is True
    assert resumen.get("eventos", {}).get("activos") == 0
    assert "No hay eventos activos" in str(resumen.get("eventos", {}).get("prioritario_nombre") or "")
    assert resultado.get("datos_reales_modificados") is False


def test_executive_diario_restaurante_con_evento_menu_incompleto_prioriza_menu(tmp_path) -> None:
    _write_json(tmp_path / "DATOS" / "db" / "planes_produccion.json", [{"id": "P1", "estado": "pendiente"}])
    _write_json(tmp_path / "DATOS" / "db" / "stock_inicial.json", [{"codigo": "A", "stock_actual": 5, "stock_minimo": 1}])
    core = _CoreFake(
        [_EventoFake(evento_id="EV1", nombre="Prueba IA", fecha="2026-10-22", pax=80)],
        {"EV1": ["Hay pases sin recetas."]},
        [{"id": "CP1", "estado": "pendiente"}],
    )

    resultado = HostAIExecutive(tmp_path).analizar_restaurante(core=core)
    resumen = dict(resultado.get("resumen_restaurante") or {})

    assert resumen.get("eventos", {}).get("activos") == 1
    assert "Prueba IA" in str(resumen.get("eventos", {}).get("prioritario_nombre") or "")
    assert "Completar el menú" in str(resumen.get("prioridad_dia", {}).get("mensaje") or "")
    assert "menú completamente preparado" in str(resumen.get("riesgo_principal") or "")
    assert resultado.get("datos_reales_modificados") is False


def test_executive_diario_restaurante_prioridad_produccion_pendiente(tmp_path) -> None:
    _write_json(tmp_path / "DATOS" / "db" / "planes_produccion.json", [{"id": "P1", "estado": "pendiente"}])
    _write_json(tmp_path / "DATOS" / "db" / "stock_inicial.json", [{"codigo": "A", "stock_actual": 3, "stock_minimo": 1}])
    core = _CoreFake(
        [_EventoFake(evento_id="EV2", nombre="Servicio Diario", fecha="2026-10-22", pax=40)],
        {"EV2": []},
        [],
    )

    resultado = HostAIExecutive(tmp_path).analizar_restaurante(core=core)
    prioridad = dict((resultado.get("resumen_restaurante") or {}).get("prioridad_dia") or {})
    assert "planificación de cocina" in str(prioridad.get("mensaje") or "")


def test_executive_diario_restaurante_prioridad_compras_pendientes(tmp_path) -> None:
    _write_json(tmp_path / "DATOS" / "db" / "planes_produccion.json", [])
    _write_json(tmp_path / "DATOS" / "db" / "stock_inicial.json", [{"codigo": "A", "stock_actual": 3, "stock_minimo": 1}])
    core = _CoreFake(
        [_EventoFake(evento_id="EV3", nombre="Evento Compras", fecha="2026-10-23", pax=50)],
        {"EV3": []},
        [{"id": "CP2", "estado": "pendiente"}],
    )

    resultado = HostAIExecutive(tmp_path).analizar_restaurante(core=core)
    prioridad = dict((resultado.get("resumen_restaurante") or {}).get("prioridad_dia") or {})
    assert "propuesta de compras" in str(prioridad.get("mensaje") or "")


def test_executive_diario_restaurante_sin_incidencias(tmp_path) -> None:
    _write_json(tmp_path / "DATOS" / "db" / "planes_produccion.json", [])
    _write_json(tmp_path / "DATOS" / "db" / "stock_inicial.json", [{"codigo": "A", "stock_actual": 10, "stock_minimo": 1}])
    core = _CoreFake(
        [_EventoFake(evento_id="EV4", nombre="Evento Estable", fecha="2026-10-24", pax=30)],
        {"EV4": []},
        [],
    )

    resultado = HostAIExecutive(tmp_path).analizar_restaurante(core=core)
    resumen = dict(resultado.get("resumen_restaurante") or {})
    assert int(resumen.get("stock", {}).get("incidencias_abiertas") or 0) == 0
    assert "No hay incidencias graves detectadas" in str(resumen.get("riesgo_principal") or "")


def test_executive_diario_restaurante_formato_conversacional(tmp_path) -> None:
    _write_json(tmp_path / "DATOS" / "db" / "planes_produccion.json", [])
    _write_json(tmp_path / "DATOS" / "db" / "stock_inicial.json", [{"codigo": "A", "stock_actual": 10, "stock_minimo": 1}])
    core = _CoreFake(
        [_EventoFake(evento_id="EV5", nombre="Prueba IA", fecha="2026-10-24", pax=30)],
        {"EV5": ["Hay pases sin recetas."]},
        [{"id": "CP3", "estado": "pendiente"}],
    )

    resultado = HostAIExecutive(tmp_path).analizar_restaurante(core=core)
    texto = formatear_respuesta_executive_conversacional(resultado, EXEC_INTENCION_RESTAURANTE)

    assert "situación general" in texto.lower() or "situacion general" in texto.lower()
    assert "prioridad del día" in texto.lower() or "prioridad del dia" in texto.lower()
    assert "Modo seguro activado" in texto


def test_executive_focus_explicacion_prioridad(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    datos = dict(DATOS_EVENTO)
    datos["id"] = "EVT-FOCUS-PRIO"
    resultado = servicio.analizar_evento(datos)

    txt = explicar_impacto_operativo(resultado, EXEC_INTENCION_MOTIVO_PRIORIDAD)
    assert "prioridad" in txt.lower() or "dependen" in txt.lower()
    assert "menú" in txt.lower() or "menu" in txt.lower() or "planificación" in txt.lower()
    assert resultado.get("datos_reales_modificados") is False


def test_executive_focus_bloqueo_produccion(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    datos = dict(DATOS_EVENTO)
    datos["id"] = "EVT-FOCUS-BLOQ"
    resultado = servicio.analizar_evento(datos)

    txt = explicar_impacto_operativo(resultado, EXEC_INTENCION_BLOQUEO_PRODUCCION)
    assert "bloqueada" in txt.lower() or "pendiente" in txt.lower()


def test_executive_focus_impacto_compras(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    datos = dict(DATOS_EVENTO)
    datos["id"] = "EVT-FOCUS-COMP"
    resultado = servicio.analizar_evento(datos)

    txt = explicar_impacto_operativo(resultado, EXEC_INTENCION_IMPACTO_COMPRAS)
    assert "propuesta de compras" in txt.lower() or "compras" in txt.lower()


def test_executive_focus_impacto_produccion(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    datos = dict(DATOS_EVENTO)
    datos["id"] = "EVT-FOCUS-PROD"
    resultado = servicio.analizar_evento(datos)

    txt = explicar_impacto_operativo(resultado, EXEC_INTENCION_IMPACTO_PRODUCCION)
    assert "producción" in txt.lower() or "produccion" in txt.lower()


def test_executive_focus_desbloqueo_mas_trabajo(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    datos = dict(DATOS_EVENTO)
    datos["id"] = "EVT-FOCUS-DESB"
    resultado = servicio.analizar_evento(datos)

    txt = explicar_impacto_operativo(resultado, EXEC_INTENCION_DESBLOQUEO)
    assert "desbloquea" in txt.lower()
    assert "•" in txt or "paso" in txt.lower()


def _resultado_evento_plan(
    *,
    evento_id: str,
    pendientes: list[str],
    workflow_prioridad: str,
    completados: list[str] | None = None,
) -> dict:
    pendientes_payload = [{"codigo": c, "paso": c, "modifica_datos": True} for c in pendientes]
    pasos_flujo = []
    for c in pendientes:
        estado = "completado" if c in set(completados or []) else "pendiente"
        pasos_flujo.append({"codigo": c, "estado": estado})
    return {
        "ok": True,
        "estado": "analisis_completo",
        "evento": {"id": evento_id, "nombre": "Evento Plan"},
        "pendientes": pendientes_payload,
        "prioridad_inmediata": {"workflow": workflow_prioridad, "titulo": "Prioridad"},
        "riesgos_operativos": ["La propuesta de compras aún no ha sido revisada."],
        "flujo": {"pasos": pasos_flujo},
        "datos_reales_modificados": False,
    }


def test_action_plan_menu_incompleto(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    resultado = _resultado_evento_plan(
        evento_id="EVT-PLAN-1",
        pendientes=["MENU_ASOCIAR", "PRODUCCION_PLAN", "COMPRAS_PREPARAR", "STOCK_REVISAR"],
        workflow_prioridad="PREPARACION_EVENTO",
    )

    plan = servicio.generar_plan_operativo(resultado, tipo_plan="evento")
    codigos = [str(p.get("codigo_origen") or "") for p in list(plan.get("pasos") or [])]
    assert plan.get("estado") == "plan_operativo_generado"
    assert plan.get("tipo_plan") == "evento"
    assert codigos[:4] == ["MENU_ASOCIAR", "PRODUCCION_PLAN", "COMPRAS_PREPARAR", "STOCK_REVISAR"]


def test_action_plan_menu_completo_y_produccion_pendiente(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    resultado = _resultado_evento_plan(
        evento_id="EVT-PLAN-2",
        pendientes=["PRODUCCION_PLAN", "COMPRAS_PREPARAR", "STOCK_REVISAR"],
        workflow_prioridad="PRODUCCION_INTELIGENTE",
    )

    plan = servicio.generar_plan_operativo(resultado, tipo_plan="evento")
    codigos = [str(p.get("codigo_origen") or "") for p in list(plan.get("pasos") or [])]
    assert codigos[0] == "PRODUCCION_PLAN"
    assert "MENU_ASOCIAR" not in codigos


def test_action_plan_compras_pendientes(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    resultado = _resultado_evento_plan(
        evento_id="EVT-PLAN-3",
        pendientes=["COMPRAS_PREPARAR", "STOCK_REVISAR"],
        workflow_prioridad="COMPRAS_INTELIGENTES",
    )

    plan = servicio.generar_plan_operativo(resultado, tipo_plan="evento")
    assert str(plan.get("pasos", [])[0].get("codigo_origen") or "") == "COMPRAS_PREPARAR"


def test_action_plan_incidencia_stock(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    resultado = _resultado_evento_plan(
        evento_id="EVT-PLAN-4",
        pendientes=["STOCK_REVISAR"],
        workflow_prioridad="STOCK_OPERATIVO",
    )

    plan = servicio.generar_plan_operativo(resultado, tipo_plan="evento")
    paso = dict(plan.get("pasos", [])[0] or {})
    assert paso.get("codigo_origen") == "STOCK_REVISAR"
    assert "stock" in str(paso.get("accion") or "").lower()


def test_action_plan_diario_restaurante(tmp_path) -> None:
    _write_json(tmp_path / "DATOS" / "db" / "planes_produccion.json", [{"id": "P1", "estado": "pendiente"}])
    _write_json(tmp_path / "DATOS" / "db" / "stock_inicial.json", [{"codigo": "A", "stock_actual": 2, "stock_minimo": 5}])
    core = _CoreFake(
        [_EventoFake(evento_id="EV-PLAN-DIA", nombre="Plan Diario", fecha="2026-10-27", pax=40)],
        {"EV-PLAN-DIA": []},
        [{"id": "CP-PLAN", "estado": "pendiente"}],
    )

    servicio = HostAIExecutive(tmp_path)
    resultado_rest = servicio.analizar_restaurante(core=core)
    plan = servicio.generar_plan_operativo(resultado_rest, tipo_plan="restaurante")

    assert plan.get("tipo_plan") == "restaurante"
    assert len(list(plan.get("pasos") or [])) >= 1


def test_action_plan_prioridad_como_primer_paso(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    resultado = _resultado_evento_plan(
        evento_id="EVT-PLAN-5",
        pendientes=["MENU_ASOCIAR", "PRODUCCION_PLAN", "COMPRAS_PREPARAR"],
        workflow_prioridad="PREPARACION_EVENTO",
    )
    plan = servicio.generar_plan_operativo(resultado, tipo_plan="evento")
    pasos = list(plan.get("pasos") or [])
    assert pasos
    assert str(pasos[0].get("codigo_origen") or "") == "MENU_ASOCIAR"


def test_action_plan_respeta_dependencias_en_orden(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    resultado = _resultado_evento_plan(
        evento_id="EVT-PLAN-6",
        pendientes=["STOCK_REVISAR", "COMPRAS_PREPARAR", "PRODUCCION_PLAN", "MENU_ASOCIAR"],
        workflow_prioridad="PREPARACION_EVENTO",
    )
    plan = servicio.generar_plan_operativo(resultado, tipo_plan="evento")
    codigos = [str(p.get("codigo_origen") or "") for p in list(plan.get("pasos") or [])]
    assert codigos.index("MENU_ASOCIAR") < codigos.index("PRODUCCION_PLAN")
    assert codigos.index("PRODUCCION_PLAN") < codigos.index("COMPRAS_PREPARAR")
    assert codigos.index("COMPRAS_PREPARAR") < codigos.index("STOCK_REVISAR")


def test_action_plan_maximo_5_pasos(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    resultado = _resultado_evento_plan(
        evento_id="EVT-PLAN-7",
        pendientes=["MENU_ASOCIAR", "PRODUCCION_PLAN", "PLANNING_GENERAR", "RECURSOS_REVISAR", "COMPRAS_PREPARAR", "STOCK_REVISAR"],
        workflow_prioridad="PREPARACION_EVENTO",
    )
    plan = servicio.generar_plan_operativo(resultado, tipo_plan="evento")
    assert 1 <= len(list(plan.get("pasos") or [])) <= 5


def test_action_plan_no_incluye_tareas_completadas(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    resultado = _resultado_evento_plan(
        evento_id="EVT-PLAN-8",
        pendientes=["MENU_ASOCIAR", "PRODUCCION_PLAN"],
        workflow_prioridad="PREPARACION_EVENTO",
        completados=["MENU_ASOCIAR"],
    )
    plan = servicio.generar_plan_operativo(resultado, tipo_plan="evento")
    codigos = [str(p.get("codigo_origen") or "") for p in list(plan.get("pasos") or [])]
    assert "MENU_ASOCIAR" not in codigos
    assert "PRODUCCION_PLAN" in codigos


def test_action_plan_no_incluye_confirmar_evento_si_existe(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    resultado = _resultado_evento_plan(
        evento_id="EVT-PLAN-9",
        pendientes=["EVENTO_CREAR", "MENU_ASOCIAR", "PRODUCCION_PLAN"],
        workflow_prioridad="PREPARACION_EVENTO",
    )
    plan = servicio.generar_plan_operativo(resultado, tipo_plan="evento")
    codigos = [str(p.get("codigo_origen") or "") for p in list(plan.get("pasos") or [])]
    assert "EVENTO_CREAR" not in codigos


def test_action_plan_vacio_si_no_hay_pendientes(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    resultado = {
        "ok": True,
        "estado": "analisis_completo",
        "evento": {"id": "EVT-PLAN-10"},
        "pendientes": [],
        "riesgos_operativos": [],
        "prioridad_inmediata": {"workflow": "GOBERNANZA", "titulo": "Seguimiento"},
        "datos_reales_modificados": False,
    }

    plan = servicio.generar_plan_operativo(resultado, tipo_plan="evento")
    assert list(plan.get("pasos") or []) == []
    assert "No hay acciones operativas pendientes" in str(plan.get("mensaje_cierre") or "")
    assert plan.get("datos_reales_modificados") is False


def test_action_plan_respuesta_conversacional_especifica(tmp_path) -> None:
    servicio = HostAIExecutive(tmp_path)
    resultado = _resultado_evento_plan(
        evento_id="EVT-PLAN-11",
        pendientes=["MENU_ASOCIAR", "PRODUCCION_PLAN", "COMPRAS_PREPARAR"],
        workflow_prioridad="PREPARACION_EVENTO",
    )
    resultado["plan_operativo"] = servicio.generar_plan_operativo(resultado, tipo_plan="evento")

    texto = formatear_respuesta_executive_conversacional(resultado, EXEC_INTENCION_PLAN_OPERATIVO)
    assert "PLAN OPERATIVO RECOMENDADO" in texto
    assert "HOST AI EXECUTIVE" not in texto
    assert "Riesgos:" not in texto
    assert "Modo seguro activado" in texto
    assert "datos_reales_modificados=False" in texto


def test_action_plan_conversacional_diario(tmp_path) -> None:
    _write_json(tmp_path / "DATOS" / "db" / "planes_produccion.json", [{"id": "P1", "estado": "pendiente"}])
    _write_json(tmp_path / "DATOS" / "db" / "stock_inicial.json", [{"codigo": "A", "stock_actual": 1, "stock_minimo": 2}])
    core = _CoreFake(
        [_EventoFake(evento_id="EV-PLAN-DIA2", nombre="Plan Diario 2", fecha="2026-10-27", pax=40)],
        {"EV-PLAN-DIA2": []},
        [{"id": "CP-PLAN2", "estado": "pendiente"}],
    )

    servicio = HostAIExecutive(tmp_path)
    resultado_rest = servicio.analizar_restaurante(core=core)
    resultado_rest["plan_operativo"] = servicio.generar_plan_operativo(resultado_rest, tipo_plan="restaurante")

    texto = formatear_respuesta_executive_conversacional(resultado_rest, EXEC_INTENCION_PLAN_DIA)
    assert "PLAN OPERATIVO RECOMENDADO" in texto or "No hay acciones operativas pendientes" in texto
    assert "Prioridad inmediata:" not in texto


def test_action_plan_evento_no_ejecuta_workflows(tmp_path, monkeypatch) -> None:
    servicio = HostAIExecutive(tmp_path)

    def _no_debe_llamarse(*_args, **_kwargs):
        raise AssertionError("No debe ejecutarse workflow en plan operativo")

    monkeypatch.setattr(servicio.orquestador_flujo, "iniciar_flujo_operativo", _no_debe_llamarse)
    monkeypatch.setattr(servicio.orquestador_flujo, "ejecutar_flujo_seguro", _no_debe_llamarse)
    monkeypatch.setattr(servicio.orquestador_flujo, "ejecutar_paso_seguro", _no_debe_llamarse)

    resultado = servicio.analizar_evento_para_plan({"id": "EVT-PLAN-NOWF", "nombre": "Evento"}, core=None)
    plan = servicio.generar_plan_operativo(resultado, tipo_plan="evento")

    assert resultado.get("ok") is True
    assert resultado.get("datos_reales_modificados") is False
    assert plan.get("datos_reales_modificados") is False
