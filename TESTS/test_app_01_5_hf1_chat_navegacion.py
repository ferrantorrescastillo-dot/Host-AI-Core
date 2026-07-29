from __future__ import annotations

import hashlib
from pathlib import Path

from APP.app_shell_host_ai import ActivityItem, AppShellHostAI
from CORE.host_ai_core import HostAICore
from TESTS.test_app_01_5_home_chat_deterministic import _seed_datos
from SERVICIOS.host_ai_home_read_service import HostAIHomeReadService


def _sha(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_consulta_eventos_no_abre_modulo_y_ofrece_accion(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    _seed_datos(shell.core)

    r = shell.chat.enviar("que eventos hay?")

    assert r["ok"] is True
    assert r["datos"]["intent"]["intent"] == "MOSTRAR_EVENTOS_PROXIMOS"
    assert not r["datos"].get("navigation_request")
    acciones = list(r["datos"].get("suggested_actions") or [])
    assert len(acciones) >= 1


def test_abrir_eventos_genera_navigation_request(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))

    r = shell.chat.enviar("abre eventos")

    nav = dict((r.get("datos") or {}).get("navigation_request") or {})
    assert nav.get("target_module") == "EVENTOS"
    assert nav.get("preserve_chat_session") is True


def test_chat_ui_no_llama_directo_eventos_en_consulta(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    _seed_datos(shell.core)
    llamadas: list[str] = []

    shell.app._menu_eventos = lambda: llamadas.append("eventos")
    entradas = iter(["que eventos hay?", "0", ""])
    shell._chat_panel(input_fn=lambda _p="": next(entradas), print_fn=lambda *_: None)

    assert llamadas == []


def test_navigation_request_se_procesa_en_shell(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    llamadas: list[str] = []
    shell._navegar = lambda op, _pf: llamadas.append(op)
    shell._pending_navigation_request = {
        "target_module": "EVENTOS",
        "preserve_chat_session": True,
    }

    shell._procesar_navegacion_pendiente(lambda *_: None)

    assert llamadas == ["2"]


def test_shell_abre_eventos_desde_navegacion(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    llamadas: list[str] = []
    shell.app._menu_eventos = lambda: llamadas.append("eventos")

    shell._navegar("2", lambda *_: None)

    assert llamadas == ["eventos"]


def test_cerrar_eventos_recupera_ruta_coherente(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    shell._active_sidebar = "1"
    shell.app._menu_eventos = lambda: None

    shell._navegar("2", lambda *_: None)

    assert shell._active_sidebar == "1"


def test_home_no_muestra_eventos_como_activo_tras_volver(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    shell.app._menu_eventos = lambda: None
    out: list[str] = []

    shell._navegar("2", lambda *_: None)
    shell._render_shell(lambda *a: out.append(" ".join(map(str, a))))

    texto = "\n".join(out)
    assert "* 1. Inicio / Host AI" in texto
    assert "* 2. Eventos" not in texto


def test_enter_vacio_sale_chat(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    entradas = iter([""])
    shell._chat_panel(input_fn=lambda _p="": next(entradas), print_fn=lambda *_: None)
    assert True


def test_volver_sale_chat(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    entradas = iter(["/volver"])
    shell._chat_panel(input_fn=lambda _p="": next(entradas), print_fn=lambda *_: None)
    assert True


def test_cero_en_menu_accion_no_se_convierte_en_mensaje(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    _seed_datos(shell.core)
    entradas = iter(["que eventos hay?", "0", ""])

    shell._chat_panel(input_fn=lambda _p="": next(entradas), print_fn=lambda *_: None)

    historial = shell.chat.historial()
    mensajes_usuario = [m for m in historial if str(m.get("rol")) == "usuario"]
    assert len(mensajes_usuario) == 1


def test_sesion_chat_se_conserva_tras_navegacion(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    shell.app._menu_eventos = lambda: None
    entradas = iter(["abre eventos"])

    shell._chat_panel(input_fn=lambda _p="": next(entradas), print_fn=lambda *_: None)
    shell._procesar_navegacion_pendiente(lambda *_: None)

    estado = shell.chat.estado_sesion()
    assert estado.get("ultima_intencion") == "ABRIR_MODULO"
    assert len(shell.chat.historial()) >= 2


def test_activity_item_normaliza_mensaje_y_texto():
    a = ActivityItem.from_chat({"tipo_mensaje": "RESULTADO", "mensaje": "ok", "timestamp": "2026-01-01T00:00:00"})
    b = ActivityItem.from_chat({"tipo": "RESULTADO", "texto": "ok2", "timestamp": "2026-01-01T00:00:00"})

    assert a is not None and a.message == "ok"
    assert b is not None and b.message == "ok2"


def test_actividad_malformada_no_rompe_home(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    shell.chat.historial = lambda: [{}]
    out: list[str] = []

    shell._render_home(lambda *a: out.append(" ".join(map(str, a))))

    texto = "\n".join(out)
    assert "Actividad no disponible" in texto


def test_no_aparece_error_tecnico_mensaje_en_home(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    shell.chat.historial = lambda: [{"rol": "host_ai", "texto": "ok"}]
    out: list[str] = []

    shell._render_shell(lambda *a: out.append(" ".join(map(str, a))))

    texto = "\n".join(out)
    assert "'mensaje'" not in texto


def test_pluralizacion_singular_produccion_bloqueada(tmp_path: Path):
    service = HostAIHomeReadService(HostAICore(tmp_path))
    modulos = {
        "recetas": {"total": 0},
        "escandallos": {"total": 0},
        "incidencias": {"total": 0},
        "eventos": {"items": []},
        "stock": {"items": []},
        "produccion": {"items": [{"bloqueadas": 1}]},
    }

    cards = service._build_bandeja(modulos)
    titulos = [c["titulo"] for c in cards if c.get("tipo") == "PRODUCCION_BLOQUEADA"]
    assert titulos and titulos[0] == "Hay 1 tarea de produccion bloqueada."


def test_pluralizacion_plural_produccion_bloqueada(tmp_path: Path):
    service = HostAIHomeReadService(HostAICore(tmp_path))
    modulos = {
        "recetas": {"total": 0},
        "escandallos": {"total": 0},
        "incidencias": {"total": 0},
        "eventos": {"items": []},
        "stock": {"items": []},
        "produccion": {"items": [{"bloqueadas": 2}]},
    }

    cards = service._build_bandeja(modulos)
    titulos = [c["titulo"] for c in cards if c.get("tipo") == "PRODUCCION_BLOQUEADA"]
    assert titulos and titulos[0] == "Hay 2 tareas de produccion bloqueadas."


def test_chat_no_escribe_datos_negocio_y_no_ia_externa(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    _seed_datos(shell.core)

    rutas = [
        shell.core.base_dir / "DATOS" / "db" / "eventos.json",
        shell.core.base_dir / "DATOS" / "db" / "biblioteca_recetas_601.json",
        shell.core.base_dir / "DATOS" / "db" / "biblioteca_escandallos_601.json",
    ]
    before = {str(r): _sha(r) for r in rutas}

    r = shell.chat.enviar("abre eventos")
    after = {str(r): _sha(r) for r in rutas}

    assert before == after
    assert ((r.get("datos") or {}).get("engine") or {}).get("proveedor") == "SIMULADO"
