from __future__ import annotations

import hashlib
from datetime import date, timedelta
from pathlib import Path

from CORE.host_ai_core import HostAICore
from APP.app_shell_host_ai import AppShellHostAI
from SERVICIOS.biblioteca_escandallos_601 import RepositorioBibliotecaEscandallos601
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.centro_importacion_601 import RepositorioCentroImportacion601
from SERVICIOS.host_ai_home_read_service import (
    ESTADO_DATOS,
    ESTADO_ERROR_PARCIAL,
    HostAIHomeReadService,
)
from SERVICIOS.host_ai_deterministic_intent_router import (
    INTENT_ABRIR_MODULO,
    INTENT_BUSCAR_RECETA,
    INTENT_DESCONOCIDA,
    HostAIDeterministicIntentRouter,
)


def _sha(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_datos(core: HostAICore) -> None:
    manana = (date.today() + timedelta(days=1)).isoformat()
    core.orquestador.resolver(
        type("S", (), {"intencion": "crear_evento", "parametros": {"nombre": "Evento APP-01.5", "fecha": manana, "pax": 80}})()
    )
    core.orquestador.resolver(
        type(
            "S",
            (),
            {
                "intencion": "registrar_necesidad_compra",
                "parametros": {
                    "nombre": "Tomate pera",
                    "cantidad": 5,
                    "unidad": "kg",
                    "motivo": "Preparacion diaria",
                    "prioridad": 90,
                },
            },
        )()
    )

    core.stock.ajustar_minimo("Tomate pera", 10)
    core.stock.registrar_entrada("Tomate pera", 2, "kg", "entrada inicial")

    repo_rec = RepositorioBibliotecaRecetas601(core.base_dir)
    repo_rec.crear(
        {
            "nombre": "Paella APP 015",
            "numero_raciones": 4,
            "ingredientes": ["Arroz"],
            "cantidades": ["0.5 kg"],
            "elaboracion": "Cocer y terminar",
        }
    )

    repo_esc = RepositorioBibliotecaEscandallos601(core.base_dir)
    repo_esc.guardar_nuevo({"nombre": "Escandallo APP 015", "estado": "DESACTUALIZADO", "lineas": []})

    repo_imp = RepositorioCentroImportacion601(core.base_dir)
    imp = repo_imp.registrar_importacion({"origen": "TEXTO", "numero_recetas": 1, "numero_incidencias": 1, "estado": "CON_INCIDENCIAS"})
    repo_imp.registrar_incidencias(imp["id"], [{"tipo": "PRODUCTO_INEXISTENTE", "detalle": "Falta producto"}])


def test_home_read_carga_datos_reales_solo_lectura(tmp_path: Path):
    core = HostAICore(tmp_path)
    _seed_datos(core)

    servicio = HostAIHomeReadService(core)
    data = servicio.cargar_home()

    assert data["estado_global"] in {ESTADO_DATOS, ESTADO_ERROR_PARCIAL}
    assert data["modulos"]["eventos"]["total"] >= 1
    assert data["modulos"]["recetas"]["total"] >= 1
    assert data["modulos"]["escandallos"]["total"] >= 1
    assert data["modulos"]["incidencias"]["total"] >= 1


def test_home_fallo_parcial_no_bloquea_total(tmp_path: Path, monkeypatch):
    core = HostAICore(tmp_path)
    _seed_datos(core)
    servicio = HostAIHomeReadService(core)

    monkeypatch.setattr(servicio, "_leer_compras_abiertas", lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    data = servicio.cargar_home()
    assert data["estado_global"] == ESTADO_ERROR_PARCIAL
    assert data["modulos"]["compras"]["estado"] == "error_parcial"
    assert data["modulos"]["eventos"]["estado"] in {"datos_disponibles", "sin_datos"}


def test_home_eventos_expone_resumen_y_avisos_reales(tmp_path: Path):
    core = HostAICore(tmp_path)
    fecha = (date.today() + timedelta(days=2)).isoformat()
    evento = core.eventos.crear_evento(
        "Boda Eventos Web",
        fecha,
        120,
        estado="confirmado",
    )
    core.eventos.agregar_servicio(
        evento.id,
        "Cena",
        "cena",
        "20:00",
        240,
    )

    modulo = HostAIHomeReadService(core)._leer_eventos_proximos()

    assert modulo["estado"] == "datos_disponibles"
    assert modulo["total"] == 1
    assert modulo["eventos_activos"] == 1
    assert modulo["total_servicios"] == 1
    assert modulo["total_avisos"] == 1
    assert modulo["resumen"] == {
        "eventos_activos": 1,
        "pax_total": 120,
        "servicios": 1,
        "avisos": 1,
    }
    assert modulo["items"][0]["estado"] == "confirmado"
    assert modulo["items"][0]["avisos"] == ["Hay servicios sin pases."]
    assert modulo["items"][0]["riesgos"] == ["Hay servicios sin pases."]
    assert modulo["items"][0]["estado_operativo"] == "revisar"


def test_home_eventos_sin_datos_conserva_contrato(tmp_path: Path):
    modulo = HostAIHomeReadService(
        HostAICore(tmp_path)
    )._leer_eventos_proximos()

    assert modulo == {
        "estado": "sin_datos",
        "total": 0,
        "items": [],
        "eventos_activos": 0,
        "total_servicios": 0,
        "total_avisos": 0,
        "resumen": {
            "eventos_activos": 0,
            "pax_total": 0,
            "servicios": 0,
            "avisos": 0,
        },
    }


def test_home_eventos_error_controlado_no_bloquea_dashboard(
    tmp_path: Path,
    monkeypatch,
):
    core = HostAICore(tmp_path)
    core.eventos.crear_evento(
        "Evento con error",
        (date.today() + timedelta(days=1)).isoformat(),
        20,
    )
    monkeypatch.setattr(
        core.eventos,
        "resumen_ejecutivo",
        lambda evento_id: (_ for _ in ()).throw(RuntimeError("error eventos")),
    )

    data = HostAIHomeReadService(core).cargar_home()

    assert data["modulos"]["eventos"] == {
        "estado": "error_parcial",
        "total": 0,
        "items": [],
        "mensaje": "Error de lectura del modulo.",
    }
    assert {"modulo": "eventos", "error": "error eventos"} in data["errores"]


def test_home_compras_expone_fuentes_reales_existentes(tmp_path: Path):
    core = HostAICore(tmp_path)
    core.compras.necesidades["NEC-1"] = type(
        "NecesidadFake",
        (),
        {
            "prioridad": 90,
            "fecha_necesaria": "2026-08-01",
            "nombre": "Tomate",
            "estado": "pendiente",
            "to_dict": lambda self: {
                "id": "NEC-1",
                "nombre": "Tomate",
                "prioridad": 90,
                "estado": "pendiente",
                "fecha_necesaria": "2026-08-01",
            },
        },
    )()
    core.compras.propuestas_compra["PROP-1"] = type(
        "PropuestaFake",
        (),
        {
            "estado": "pendiente",
            "creado_en": "2026-07-29T10:00:00",
            "id": "PROP-1",
            "to_dict": lambda self: {
                "id": "PROP-1",
                "producto": "Tomate",
                "comprar": 5,
                "unidad": "kg",
                "prioridad": "Alta",
                "estado": "pendiente",
                "creado_en": "2026-07-29T10:00:00",
            },
        },
    )()
    core.compras.listar_propuestas_compra = lambda solo_pendientes=True: [
        core.compras.propuestas_compra["PROP-1"].to_dict()
    ]
    core.compras.listar_proveedores = lambda incluir_inactivos=False: [
        {"id": "PROV-1", "nombre": "Proveedor Uno", "estado": "activo"}
    ]
    core.compras.listar_historial_compras = lambda: [
        {
            "id": "COMPRA-1",
            "producto": "Tomate",
            "cantidad": 5,
            "unidad": "kg",
            "proveedor": "Proveedor Uno",
            "estado": "registrada",
            "creado_en": "2026-07-28T10:00:00",
        }
    ]

    modulo = HostAIHomeReadService(core)._leer_compras_abiertas()

    assert modulo["total"] == 1
    assert modulo["necesidades_pendientes"] == 1
    assert modulo["propuestas_pendientes"] == 1
    assert modulo["total_propuestas"] == 1
    assert modulo["total_proveedores"] == 1
    assert modulo["total_historial"] == 1
    assert modulo["propuestas"][0]["producto"] == "Tomate"
    assert modulo["proveedores"][0]["nombre"] == "Proveedor Uno"
    assert modulo["historial"][0]["id"] == "COMPRA-1"


def test_home_compras_sin_datos_conserva_colecciones_vacias(tmp_path: Path):
    modulo = HostAIHomeReadService(
        HostAICore(tmp_path)
    )._leer_compras_abiertas()

    assert modulo == {
        "estado": "sin_datos",
        "total": 0,
        "items": [],
        "necesidades_pendientes": 0,
        "propuestas_pendientes": 0,
        "propuestas": [],
        "proveedores": [],
        "historial": [],
        "total_propuestas": 0,
        "total_proveedores": 0,
        "total_historial": 0,
        "pedidos": [],
        "total_pedidos": 0,
    }


def test_bandeja_determinista_y_prioridad_reproducible(tmp_path: Path):
    core = HostAICore(tmp_path)
    _seed_datos(core)
    servicio = HostAIHomeReadService(core)

    data1 = servicio.cargar_home()["bandeja"]
    data2 = servicio.cargar_home()["bandeja"]

    assert data1 == data2
    if data1:
        assert data1[0]["severidad"] in {"critica", "importante", "atencion", "informacion"}
        assert all(card.get("accion_navegacion") for card in data1)


def test_chat_buscar_receta_reutiliza_servicio_existente(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    _seed_datos(shell.core)

    r = shell.chat.enviar("Busca la receta paella")

    assert r["ok"] is True
    assert r["datos"]["intent"]["intent"] == INTENT_BUSCAR_RECETA
    assert len(r["datos"].get("resultados") or []) >= 1


def test_chat_lista_recetas_escandallos_incidencias_eventos(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    _seed_datos(shell.core)

    r1 = shell.chat.enviar("muestrame las recetas pendientes")
    r2 = shell.chat.enviar("que escandallos estan desactualizados")
    r3 = shell.chat.enviar("que incidencias tengo")
    r4 = shell.chat.enviar("que eventos hay proximos")

    assert r1["ok"] and "recetas" in r1["mensaje"].lower()
    assert r2["ok"] and "escandallos" in r2["mensaje"].lower()
    assert r3["ok"] and "incidencias" in r3["mensaje"].lower()
    assert r4["ok"] and "eventos" in r4["mensaje"].lower()


def test_chat_abrir_modulo_e_intencion_desconocida(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))

    abrir = shell.chat.enviar("abre produccion")
    desconocida = shell.chat.enviar("haz una prediccion financiera avanzada")

    assert abrir["datos"]["intent"]["intent"] == INTENT_ABRIR_MODULO
    assert abrir["datos"]["accion_navegacion"]["sidebar"] == "3"
    assert desconocida["datos"]["intent"]["intent"] == INTENT_DESCONOCIDA
    assert desconocida["tipo_mensaje"] == "ADVERTENCIA"


def test_chat_activa_host_ai_executive_desde_evento_activo(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    _seed_datos(shell.core)

    eventos = list(shell.core.eventos.listar_eventos())
    assert eventos
    evento_id = str(getattr(eventos[0], "id", ""))

    db = shell.core.base_dir / "DATOS" / "db"
    rutas = [
        db / "stock_movimientos.json",
        db / "proveedores.json",
        db / "planes_produccion.json",
    ]
    before = {str(r): _sha(r) for r in rutas}

    r = shell.chat.enviar("analiza el evento actual", contexto={"evento_id": evento_id})

    assert r["ok"] is True
    assert r["tipo_mensaje"] == "RESULTADO"
    assert "HOST AI EXECUTIVE" in r["mensaje"]
    assert "Estado general:" in r["mensaje"]
    assert "Prioridad inmediata:" in r["mensaje"]
    assert "Pendientes:" in r["mensaje"]
    assert "Riesgos:" in r["mensaje"]
    assert "Recomendaciones:" in r["mensaje"]
    assert "Resumen ejecutivo:" in r["mensaje"]
    assert "Confirmar creación del evento" not in r["mensaje"]
    assert "Generar la planificación de cocina" in r["mensaje"] or "Revisar la propuesta de compras del evento" in r["mensaje"]
    datos_exec = dict((r.get("datos") or {}).get("executive") or {})
    assert datos_exec.get("estado") == "analisis_completo"
    assert datos_exec.get("datos_reales_modificados") is False
    assert isinstance(datos_exec.get("pendientes"), list)
    assert isinstance(datos_exec.get("riesgos"), list)
    assert isinstance(datos_exec.get("workflows_priorizados"), list)
    assert isinstance(datos_exec.get("recomendaciones"), list)
    assert isinstance(datos_exec.get("prioridad_inmediata"), dict)
    assert isinstance(datos_exec.get("pendientes_operativos"), list)
    assert isinstance(datos_exec.get("riesgos_operativos"), list)
    assert isinstance(datos_exec.get("recomendaciones_operativas"), list)

    after = {str(r): _sha(r) for r in rutas}
    assert before == after


def test_chat_executive_conversacional_responde_por_intencion(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    _seed_datos(shell.core)

    eventos = list(shell.core.eventos.listar_eventos())
    assert eventos
    evento_id = str(getattr(eventos[0], "id", ""))
    ctx = {"evento_id": evento_id}

    r_pend = shell.chat.enviar("que falta para este evento", contexto=ctx)
    r_urg = shell.chat.enviar("que es lo mas urgente", contexto=ctx)
    r_ries = shell.chat.enviar("que riesgos hay", contexto=ctx)
    r_rec = shell.chat.enviar("que me recomiendas", contexto=ctx)
    r_res = shell.chat.enviar("resumen ejecutivo", contexto=ctx)

    assert "HOST AI EXECUTIVE" not in r_pend["mensaje"]
    assert "Todavía quedan estas tareas" in r_pend["mensaje"]
    assert "Riesgos:" not in r_pend["mensaje"]
    assert "Cuando completes completar menú" not in r_pend["mensaje"]

    assert "HOST AI EXECUTIVE" not in r_urg["mensaje"]
    assert "prioridad" in r_urg["mensaje"].lower()
    assert "Motivo:" in r_urg["mensaje"]
    assert "Pendientes:" not in r_urg["mensaje"]
    urg_norm = r_urg["mensaje"].lower()
    assert "generar la planificación de cocina" in urg_norm or "completar el menú del evento" in urg_norm

    assert "HOST AI EXECUTIVE" not in r_ries["mensaje"]
    assert "riesgo" in r_ries["mensaje"].lower()
    assert "Recomendaciones:" not in r_ries["mensaje"]
    assert "menú no esté completo" in r_ries["mensaje"] or "planificación de cocina" in r_ries["mensaje"] or "compras" in r_ries["mensaje"].lower()

    assert "HOST AI EXECUTIVE" not in r_rec["mensaje"]
    assert "Mi recomendación" in r_rec["mensaje"]
    assert "1." in r_rec["mensaje"]
    assert "Riesgos:" not in r_rec["mensaje"]

    assert "HOST AI EXECUTIVE" not in r_res["mensaje"]
    assert len([x for x in r_res["mensaje"].splitlines() if x.strip()]) <= 5
    assert "Pendientes:" not in r_res["mensaje"]


def test_chat_executive_diario_restaurante_intencion_nueva(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    _seed_datos(shell.core)

    r = shell.chat.enviar("como esta hoy el restaurante")
    assert r["ok"] is True
    assert "situación general" in r["mensaje"].lower() or "situacion general" in r["mensaje"].lower()
    assert "prioridad del día" in r["mensaje"].lower() or "prioridad del dia" in r["mensaje"].lower()
    assert "modo seguro" in r["mensaje"].lower()

    datos_exec = dict((r.get("datos") or {}).get("executive") or {})
    assert datos_exec.get("datos_reales_modificados") is False
    assert dict(datos_exec.get("resumen_restaurante") or {}).get("eventos") is not None


def test_chat_executive_focus_intenciones_impacto(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    _seed_datos(shell.core)

    eventos = list(shell.core.eventos.listar_eventos())
    assert eventos
    evento_id = str(getattr(eventos[0], "id", ""))
    ctx = {"evento_id": evento_id}

    r1 = shell.chat.enviar("por que es la prioridad", contexto=ctx)
    r2 = shell.chat.enviar("que bloquea la produccion", contexto=ctx)
    r3 = shell.chat.enviar("que pasa si no preparo produccion", contexto=ctx)
    r4 = shell.chat.enviar("que pasa si dejo compras para manana", contexto=ctx)
    r5 = shell.chat.enviar("que desbloquea mas trabajo", contexto=ctx)

    assert "prioridad" in r1["mensaje"].lower() or "depend" in r1["mensaje"].lower()
    assert "bloque" in r2["mensaje"].lower() or "pendiente" in r2["mensaje"].lower()
    assert "producción" in r3["mensaje"].lower() or "produccion" in r3["mensaje"].lower()
    assert "compras" in r4["mensaje"].lower()
    assert "desbloquea" in r5["mensaje"].lower()

    for r in [r1, r2, r3, r4, r5]:
        datos_exec = dict((r.get("datos") or {}).get("executive") or {})
        assert datos_exec.get("datos_reales_modificados") is False


def test_chat_executive_action_plan_evento(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    _seed_datos(shell.core)

    eventos = list(shell.core.eventos.listar_eventos())
    assert eventos
    evento_id = str(getattr(eventos[0], "id", ""))
    ctx = {"evento_id": evento_id}

    r = shell.chat.enviar("hazme un plan", contexto=ctx)

    assert r["ok"] is True
    assert "PLAN OPERATIVO RECOMENDADO" in r["mensaje"] or "No hay acciones operativas pendientes" in r["mensaje"]
    assert "HOST AI EXECUTIVE" not in r["mensaje"]
    assert "Riesgos:" not in r["mensaje"]
    assert "datos_reales_modificados=False" in r["mensaje"]

    datos_exec = dict((r.get("datos") or {}).get("executive") or {})
    plan = dict(datos_exec.get("plan_operativo") or {})
    pasos = list(plan.get("pasos") or [])
    assert plan.get("estado") == "plan_operativo_generado"
    assert plan.get("tipo_plan") == "evento"
    assert len(pasos) <= 5
    assert plan.get("datos_reales_modificados") is False


def test_chat_executive_action_plan_dia_global(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    _seed_datos(shell.core)

    r = shell.chat.enviar("cual es el plan de hoy")

    assert r["ok"] is True
    assert "PLAN OPERATIVO RECOMENDADO" in r["mensaje"] or "No hay acciones operativas pendientes" in r["mensaje"]
    datos_exec = dict((r.get("datos") or {}).get("executive") or {})
    plan = dict(datos_exec.get("plan_operativo") or {})
    assert plan.get("tipo_plan") == "restaurante"
    assert plan.get("datos_reales_modificados") is False


def test_router_patrones_reconocidos_y_desconocidos():
    router = HostAIDeterministicIntentRouter()

    assert router.detectar("Buscar receta de ensaladilla").intent == INTENT_BUSCAR_RECETA
    assert router.detectar("Llevame a compras").intent == INTENT_ABRIR_MODULO
    assert router.detectar("texto raro sin patron").intent == INTENT_DESCONOCIDA


def test_chat_no_escribe_datos_negocio(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    _seed_datos(shell.core)

    rutas = [
        shell.core.base_dir / "DATOS" / "db" / "eventos.json",
        shell.core.base_dir / "DATOS" / "db" / "biblioteca_recetas_601.json",
        shell.core.base_dir / "DATOS" / "db" / "biblioteca_escandallos_601.json",
    ]
    before = {str(r): _sha(r) for r in rutas}

    shell.chat.enviar("que eventos hay proximos")
    shell.chat.enviar("busca la receta paella")
    shell.chat.enviar("que incidencias tengo")

    after = {str(r): _sha(r) for r in rutas}
    assert before == after


def test_ui_no_accede_persistencia_directa_y_sin_proveedores_externos():
    base = Path(__file__).resolve().parents[1]
    shell_src = (base / "APP" / "app_shell_host_ai.py").read_text(encoding="utf-8")
    chat_src = (base / "SERVICIOS" / "chat_host_ai_shell_service.py").read_text(encoding="utf-8")

    assert "DATOS/db" not in shell_src
    assert "SimulatedProvider" not in shell_src
    assert "NotConnectedProvider" not in shell_src
    assert "proveedor_preferido" in chat_src
    assert "SIMULADO" in chat_src


def test_proveedor_activo_sigue_simulado(tmp_path: Path):
    core = HostAICore(tmp_path)
    shell = AppShellHostAI(core)

    r = shell.chat.enviar("ayuda")
    engine = dict((r.get("datos") or {}).get("engine") or {})

    assert engine.get("proveedor") == "SIMULADO"


def test_shell_navegacion_y_modulos_existentes_accesibles(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    llamadas: list[str] = []
    shell.app._menu_eventos = lambda: llamadas.append("eventos")
    shell.app._menu_produccion_real = lambda: llamadas.append("produccion")
    shell.app._menu_compras = lambda: llamadas.append("compras")

    shell._navegar("2", lambda *_: None)
    shell._navegar("3", lambda *_: None)
    shell._navegar("4", lambda *_: None)

    assert llamadas == ["eventos", "produccion", "compras"]
