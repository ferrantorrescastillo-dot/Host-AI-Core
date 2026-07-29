from __future__ import annotations

from pathlib import Path

from CORE.host_ai_core import HostAICore
from SERVICIOS.host_ai_home_read_service import HostAIHomeReadService
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
from SERVICIOS.host_ai_tool_registry import TOOL_STATUS_DESHABILITADA, build_default_tool_registry
from SERVICIOS.host_ai_tool_resolver import HostAIToolResolver
from TESTS.test_app_01_5_home_chat_deterministic import _seed_datos


def test_registry_carga_herramientas_y_writes_deshabilitadas():
    registry = build_default_tool_registry()
    stats = registry.stats()

    assert stats["total"] >= 20
    assert registry.get("buscar_recetas") is not None
    assert registry.get("crear_receta") is not None
    assert registry.get("crear_receta").estado == TOOL_STATUS_DESHABILITADA


def test_resolver_intento_a_herramienta_y_abrir_modulo():
    resolver = HostAIToolResolver()

    t1 = resolver.resolve("MOSTRAR_EVENTOS_PROXIMOS", terms={})
    t2 = resolver.resolve("ABRIR_MODULO", terms={"modulo_sidebar": "3"})

    assert t1 == "mostrar_eventos_proximos"
    assert t2 == "abrir_produccion"


def test_executor_read_navigation_y_respuesta_normalizada(tmp_path: Path):
    core = HostAICore(tmp_path)
    _seed_datos(core)
    home = HostAIHomeReadService(core)
    registry = build_default_tool_registry()
    ex = HostAIToolExecutor(registry, home_read_service=home)

    r1 = ex.execute("mostrar_eventos_proximos", params={}, session_context={"contexto_activo": "HOME"})
    r2 = ex.execute("abrir_evento", params={}, session_context={"contexto_activo": "EVENTO"})

    for r in [r1, r2]:
        d = r.to_dict()
        assert "estado" in d
        assert "mensaje" in d
        assert "datos" in d
        assert "acciones" in d
        assert "contexto_actualizado" in d
        assert "navegacion" in d
        assert "errores" in d
        assert "advertencias" in d
        assert "duracion_ms" in d

    assert r1.estado == "OK"
    assert r2.navegacion.get("target_module") == "EVENTOS"


def test_executor_herramienta_inexistente_y_deshabilitada(tmp_path: Path):
    core = HostAICore(tmp_path)
    home = HostAIHomeReadService(core)
    registry = build_default_tool_registry()
    ex = HostAIToolExecutor(registry, home_read_service=home)

    missing = ex.execute("no_existe", params={}, session_context={})
    disabled = ex.execute("crear_receta", params={}, session_context={"contexto_activo": "RECETA"})

    assert missing.estado == "ERROR"
    assert disabled.estado == "DESHABILITADA"


def test_executor_solo_lectura_no_escribe_datos(tmp_path: Path):
    core = HostAICore(tmp_path)
    _seed_datos(core)
    home = HostAIHomeReadService(core)
    registry = build_default_tool_registry()
    ex = HostAIToolExecutor(registry, home_read_service=home)

    eventos = core.base_dir / "DATOS" / "db" / "eventos.json"
    before = eventos.read_text(encoding="utf-8") if eventos.exists() else ""

    ex.execute("mostrar_eventos_proximos", params={}, session_context={"contexto_activo": "HOME"})

    after = eventos.read_text(encoding="utf-8") if eventos.exists() else ""
    assert before == after


def test_executor_actualiza_contexto_en_navigation(tmp_path: Path):
    core = HostAICore(tmp_path)
    home = HostAIHomeReadService(core)
    registry = build_default_tool_registry()
    ex = HostAIToolExecutor(registry, home_read_service=home)

    res = ex.execute("abrir_stock", params={}, session_context={"contexto_activo": "HOME"})

    assert res.navegacion.get("target_module") == "STOCK"
    assert (res.contexto_actualizado or {}).get("contexto_activo") == "STOCK"


def test_chat_depende_de_tool_framework_no_de_servicios_directos():
    base = Path(__file__).resolve().parents[1]
    src = (base / "SERVICIOS" / "chat_host_ai_shell_service.py").read_text(encoding="utf-8")

    assert "HostAIToolResolver" in src
    assert "HostAIToolExecutor" in src
    assert "tool_executor.execute(" in src
