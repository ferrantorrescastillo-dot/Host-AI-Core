from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from APP.app_shell_host_ai import AppShellHostAI
from CORE.host_ai_core import HostAICore
from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell
from SERVICIOS.contexto_activo_host_ai import ServicioContextoActivoHostAI
from SERVICIOS.host_ai_executive import HostAIExecutive


BASE_DIR = Path(__file__).resolve().parents[1]


def _core_tmp(tmp_path: Path) -> HostAICore:
    return HostAICore(tmp_path)


def test_app_01_shell_arranca_y_renderiza(tmp_path: Path):
    shell = AppShellHostAI(_core_tmp(tmp_path))
    out: list[str] = []
    entradas = iter(["0"])

    shell.ejecutar(
        input_fn=lambda _prompt="": next(entradas),
        print_fn=lambda *args: out.append(" ".join(map(str, args))),
    )

    texto = "\n".join(out)
    assert "HOST AI APP SHELL - APP-01.5" in texto
    assert "MAIN CONTENT - HOST AI HOME" in texto
    assert "HOST AI PANEL" in texto


def test_app_01_navegacion_principal_reutiliza_modulos(tmp_path: Path):
    shell = AppShellHostAI(_core_tmp(tmp_path))
    llamadas: list[str] = []

    shell.app._menu_eventos = lambda: llamadas.append("eventos")
    shell.app._menu_produccion_real = lambda: llamadas.append("produccion")
    shell.app._menu_compras = lambda: llamadas.append("compras")
    shell.app._menu_stock = lambda: llamadas.append("stock")
    shell.app._menu_escandallos_recetas = lambda: llamadas.append("escandallos")
    shell.app._menu_excel = lambda: llamadas.append("excel")

    for opcion in ["2", "3", "4", "5", "6", "9"]:
        shell._navegar(opcion, lambda *_a: None)

    assert llamadas == ["eventos", "produccion", "compras", "stock", "escandallos", "excel"]


def test_app_01_chat_usa_engine_simulado_via_orquestador(tmp_path: Path):
    shell = AppShellHostAI(_core_tmp(tmp_path))

    respuesta = shell.chat.enviar("Busca la receta de la ensaladilla", contexto={"tipo": "GENERAL"})

    assert respuesta["ok"] is True
    assert respuesta["tipo_mensaje"] in {"RESULTADO", "PROPUESTA", "CONFIRMACION", "INCIDENCIA"}

    historial = shell.chat.historial()
    assert len(historial) >= 2
    ultimo = historial[-1]
    engine = dict(ultimo.get("datos", {}).get("engine") or {})
    assert engine.get("proveedor") == "SIMULADO"


def test_app_01_chat_normaliza_error_proveedor(tmp_path: Path):
    core = _core_tmp(tmp_path)

    class _FakeOrq:
        def resolver(self, _req):
            from CORE.orquestador import RespuestaHostAI

            return RespuestaHostAI(
                ok=False,
                intencion="host_ai_engine_consulta",
                mensaje="fallo",
                datos={
                    "host_ai_engine": {
                        "estado": "ERROR",
                        "errores": ["Proveedor no conectado todavia: OPENAI"],
                        "respuesta": {},
                    }
                },
                acciones_recomendadas=[],
            )

    service = ServicioChatHostAIShell(_FakeOrq())
    r = service.enviar("prueba error")

    assert r["ok"] is False
    assert r["tipo_mensaje"] == "ERROR"
    assert "Proveedor no conectado" in r["mensaje"]


def test_app_01_chat_no_llama_proveedor_directo_desde_ui():
    contenido = (BASE_DIR / "APP" / "app_shell_host_ai.py").read_text(encoding="utf-8")
    assert "SimulatedProvider" not in contenido
    assert "NotConnectedProvider" not in contenido
    assert "host_ai_engine_consulta" in (BASE_DIR / "SERVICIOS" / "chat_host_ai_shell_service.py").read_text(encoding="utf-8")


def test_app_01_contexto_general_inicializado():
    ctx = ServicioContextoActivoHostAI().obtener()
    assert ctx.tipo == "GENERAL"
    assert ctx.etiqueta == "Contexto general"


def test_app_01_chat_limpiar_sesion(tmp_path: Path):
    shell = AppShellHostAI(_core_tmp(tmp_path))
    shell.chat.enviar("hola")
    assert len(shell.chat.historial()) >= 2
    shell.chat.limpiar()
    assert shell.chat.historial() == []


def test_app_01_no_escritura_negocio_en_chat(tmp_path: Path):
    shell = AppShellHostAI(_core_tmp(tmp_path))
    before = shell.core.base_dir / "DATOS" / "db" / "eventos.json"
    before_exists = before.exists()
    before_content = before.read_text(encoding="utf-8") if before_exists else ""

    shell.chat.enviar("consulta general de estado")

    after_exists = before.exists()
    after_content = before.read_text(encoding="utf-8") if after_exists else ""
    assert before_exists == after_exists
    assert before_content == after_content


def test_app_01_chat_executive_conversacional_reutiliza_servicio(tmp_path: Path, monkeypatch):
    shell = AppShellHostAI(_core_tmp(tmp_path))
    manana = (date.today() + timedelta(days=1)).isoformat()
    creado = shell.core.orquestador.resolver(
        type("S", (), {"intencion": "crear_evento", "parametros": {"nombre": "EVT-CHAT-EXEC", "fecha": manana, "pax": 60}})()
    )
    evento_id = str((((creado.datos or {}).get("evento") or {}).get("id") or ""))
    assert evento_id

    llamadas = {"n": 0}
    original = HostAIExecutive.analizar_evento

    def _spy(self, datos_evento):
        llamadas["n"] += 1
        return original(self, datos_evento)

    monkeypatch.setattr(HostAIExecutive, "analizar_evento", _spy)

    r = shell.chat.enviar("que me recomiendas", contexto={"evento_id": evento_id})
    assert r["ok"] is True
    assert llamadas["n"] == 1
    datos_exec = dict((r.get("datos") or {}).get("executive") or {})
    assert datos_exec.get("datos_reales_modificados") is False


def test_app_01_chat_executive_diario_funciona_sin_evento_activo(tmp_path: Path):
    shell = AppShellHostAI(_core_tmp(tmp_path))

    r = shell.chat.enviar("resumen del restaurante")
    assert r["ok"] is True
    assert "situación general" in r["mensaje"].lower() or "situacion general" in r["mensaje"].lower()
    datos_exec = dict((r.get("datos") or {}).get("executive") or {})
    assert datos_exec.get("estado") == "resumen_restaurante_generado"
    assert datos_exec.get("datos_reales_modificados") is False


def test_app_01_chat_executive_focus_sin_evento_activo(tmp_path: Path):
    shell = AppShellHostAI(_core_tmp(tmp_path))

    r = shell.chat.enviar("por que es la prioridad")
    assert r["ok"] is True
    assert "prioridad" in r["mensaje"].lower() or "depend" in r["mensaje"].lower()
    datos_exec = dict((r.get("datos") or {}).get("executive") or {})
    assert datos_exec.get("datos_reales_modificados") is False


def test_app_01_chat_executive_plan_sin_evento_activo(tmp_path: Path):
    shell = AppShellHostAI(_core_tmp(tmp_path))

    r = shell.chat.enviar("dame un plan operativo")
    assert r["ok"] is True
    assert "PLAN OPERATIVO RECOMENDADO" in r["mensaje"] or "No hay acciones operativas pendientes" in r["mensaje"]

    datos_exec = dict((r.get("datos") or {}).get("executive") or {})
    plan = dict(datos_exec.get("plan_operativo") or {})
    assert plan.get("estado") == "plan_operativo_generado"
    assert plan.get("tipo_plan") == "restaurante"
    assert plan.get("datos_reales_modificados") is False
