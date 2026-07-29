from APP.consola import AppConsolaHostAI
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI
from SERVICIOS.host_ai_executive import HostAIExecutive


def _sha(path):
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _inputs(monkeypatch, valores):
    it = iter(valores)
    monkeypatch.setattr("builtins.input", lambda _="": next(it))


def test_ux1_si_no_repregunta(monkeypatch, capsys):
    _inputs(monkeypatch, ["patata", "s"])
    assert AppConsolaHostAI._preguntar_si_no("¿Continuar?", por_defecto=False) is True
    assert "Responde 's'" in capsys.readouterr().out


def test_ux1_cancelar_necesidad_con_enter(tmp_path, monkeypatch, capsys):
    core = HostAICore(tmp_path)
    core.compras.registrar_necesidad("Tomate", 2, "kg", "Sardà")
    app = AppConsolaHostAI(core)
    _inputs(monkeypatch, [""])
    assert app._seleccionar_necesidad_compra() is None
    assert "Operación cancelada" in capsys.readouterr().out


def test_ux1_auto_selecciona_escandallo_unico(tmp_path, monkeypatch, capsys):
    core = HostAICore(tmp_path)
    core.escandallos_inteligente.registrar_escandallo("REC-UNO", "Receta única", 4, [])
    app = AppConsolaHostAI(core)
    _inputs(monkeypatch, ["receta única"])
    elegido = app._seleccionar_escandallo()
    assert elegido["receta_id"] == "REC-UNO"
    assert "seleccionado automáticamente" in capsys.readouterr().out


def test_ux1_busqueda_articulo_vacia_cancela(tmp_path, monkeypatch, capsys):
    app = AppConsolaHostAI(HostAICore(tmp_path))
    _inputs(monkeypatch, [""])
    assert app._seleccionar_articulo_stock() is None
    assert "cancelada" in capsys.readouterr().out.lower()


def test_ux1_hablar_host_ai_activa_executive_en_evento_activo(tmp_path, monkeypatch, capsys):
    core = HostAICore(tmp_path)
    creada = core.orquestador.resolver(
        SolicitudHostAI(
            "crear_evento",
            {
                "nombre": "Evento Executive UX",
                "fecha": "2026-10-22",
                "pax": 90,
                "tipo": "boda",
            },
        )
    )
    evento_id = str(((creada.datos or {}).get("evento") or {}).get("id") or "")
    assert evento_id

    app = AppConsolaHostAI(core)
    app.ultimo_evento_id = evento_id

    db = core.base_dir / "DATOS" / "db"
    rutas = [
        db / "stock_movimientos.json",
        db / "proveedores.json",
        db / "planes_produccion.json",
    ]
    before = {str(r): _sha(r) for r in rutas}

    _inputs(monkeypatch, ["analiza el evento actual", "salir"])
    app._hablar_host_ai()

    out = capsys.readouterr().out
    assert "HOST AI EXECUTIVE" in out
    assert "Estado general:" in out
    assert "Prioridad inmediata:" in out
    assert "Pendientes:" in out
    assert "Riesgos:" in out
    assert "Recomendaciones:" in out
    assert "Resumen ejecutivo:" in out
    assert "datos_reales_modificados=False" in out

    after = {str(r): _sha(r) for r in rutas}
    assert before == after


def test_ux1_hablar_host_ai_executive_responde_por_intencion(tmp_path, monkeypatch, capsys):
    core = HostAICore(tmp_path)
    creada = core.orquestador.resolver(
        SolicitudHostAI(
            "crear_evento",
            {
                "nombre": "Evento Executive UX 2",
                "fecha": "2026-10-23",
                "pax": 110,
                "tipo": "boda",
            },
        )
    )
    evento_id = str(((creada.datos or {}).get("evento") or {}).get("id") or "")
    assert evento_id

    app = AppConsolaHostAI(core)
    app.ultimo_evento_id = evento_id

    _inputs(
        monkeypatch,
        [
            "que falta",
            "que es lo mas urgente",
            "que riesgos hay",
            "que me recomiendas",
            "resumen ejecutivo",
            "salir",
        ],
    )
    app._hablar_host_ai()
    out = capsys.readouterr().out

    assert "Todavía quedan estas tareas" in out
    assert "HOST AI EXECUTIVE" not in out
    assert "Motivo:" in out
    assert "He detectado" in out or "riesgo" in out.lower()
    assert "Mi recomendación es:" in out
    assert "1." in out
    assert "Modo seguro activado" in out


def test_ux1_chat_muestra_resumen_proactivo_si_hay_evento_activo(tmp_path, monkeypatch, capsys):
    core = HostAICore(tmp_path)
    creada = core.orquestador.resolver(
        SolicitudHostAI(
            "crear_evento",
            {
                "nombre": "Prueba IA",
                "fecha": "2026-10-24",
                "pax": 70,
                "tipo": "boda",
            },
        )
    )
    evento_id = str(((creada.datos or {}).get("evento") or {}).get("id") or "")
    assert evento_id

    app = AppConsolaHostAI(core)
    app.ultimo_evento_id = evento_id

    _inputs(monkeypatch, ["salir"])
    app._hablar_host_ai()
    out = capsys.readouterr().out

    assert "He revisado el evento activo" in out
    assert "Quedan estas tareas:" in out or "No detecto tareas operativas urgentes" in out
    assert "Puedes preguntarme:" in out
    assert "Modo seguro activado." in out


def test_ux1_chat_no_muestra_resumen_proactivo_sin_evento(tmp_path, monkeypatch, capsys):
    app = AppConsolaHostAI(HostAICore(tmp_path))

    _inputs(monkeypatch, ["salir"])
    app._hablar_host_ai()
    out = capsys.readouterr().out

    assert "Habla con Host AI. Escribe 'salir' para volver." in out
    assert "He revisado el evento activo" not in out


def test_ux1_entrar_chat_no_ejecuta_workflows_ni_modifica_datos(tmp_path, monkeypatch, capsys):
    core = HostAICore(tmp_path)
    creada = core.orquestador.resolver(
        SolicitudHostAI(
            "crear_evento",
            {
                "nombre": "Evento Proactivo Seguro",
                "fecha": "2026-10-25",
                "pax": 85,
                "tipo": "boda",
            },
        )
    )
    evento_id = str(((creada.datos or {}).get("evento") or {}).get("id") or "")
    assert evento_id

    app = AppConsolaHostAI(core)
    app.ultimo_evento_id = evento_id

    llamadas = {"n": 0}
    original = HostAIExecutive.analizar_evento

    def _spy(self, datos_evento):
        llamadas["n"] += 1
        return original(self, datos_evento)

    monkeypatch.setattr(HostAIExecutive, "analizar_evento", _spy)

    db = core.base_dir / "DATOS" / "db"
    rutas = [
        db / "stock_movimientos.json",
        db / "proveedores.json",
        db / "planes_produccion.json",
        db / "compras_pedidos.json",
    ]
    before = {str(r): _sha(r) for r in rutas}

    _inputs(monkeypatch, ["salir"])
    app._hablar_host_ai()
    _ = capsys.readouterr().out

    after = {str(r): _sha(r) for r in rutas}
    assert before == after
    assert llamadas["n"] == 0


def test_ux1_hablar_host_ai_executive_diario_restaurante(tmp_path, monkeypatch, capsys):
    app = AppConsolaHostAI(HostAICore(tmp_path))

    _inputs(monkeypatch, ["panorama general", "salir"])
    app._hablar_host_ai()
    out = capsys.readouterr().out

    assert "Host AI:" in out
    assert "situación general" in out.lower() or "situacion general" in out.lower()
    assert "modo seguro" in out.lower()


def test_ux1_hablar_host_ai_executive_focus_impacto(tmp_path, monkeypatch, capsys):
    core = HostAICore(tmp_path)
    creada = core.orquestador.resolver(
        SolicitudHostAI(
            "crear_evento",
            {
                "nombre": "Evento Focus",
                "fecha": "2026-10-26",
                "pax": 65,
                "tipo": "boda",
            },
        )
    )
    evento_id = str(((creada.datos or {}).get("evento") or {}).get("id") or "")
    assert evento_id

    app = AppConsolaHostAI(core)
    app.ultimo_evento_id = evento_id

    _inputs(monkeypatch, ["que desbloquea mas trabajo", "por que es la prioridad", "salir"])
    app._hablar_host_ai()
    out = capsys.readouterr().out.lower()

    assert "desbloquea" in out
    assert "prioridad" in out or "depend" in out


def test_ux1_hablar_host_ai_executive_action_plan(tmp_path, monkeypatch, capsys):
    core = HostAICore(tmp_path)
    creada = core.orquestador.resolver(
        SolicitudHostAI(
            "crear_evento",
            {
                "nombre": "Evento Plan Consola",
                "fecha": "2026-10-27",
                "pax": 72,
                "tipo": "boda",
            },
        )
    )
    evento_id = str(((creada.datos or {}).get("evento") or {}).get("id") or "")
    assert evento_id

    app = AppConsolaHostAI(core)
    app.ultimo_evento_id = evento_id

    _inputs(monkeypatch, ["que hago ahora paso a paso", "salir"])
    app._hablar_host_ai()
    out = capsys.readouterr().out

    assert "PLAN OPERATIVO RECOMENDADO" in out or "No hay acciones operativas pendientes" in out
    assert "datos_reales_modificados=False" in out
    assert "HOST AI EXECUTIVE" not in out
