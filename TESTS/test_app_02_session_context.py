from __future__ import annotations

from pathlib import Path

from APP.app_shell_host_ai import AppShellHostAI
from CORE.host_ai_core import HostAICore
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from TESTS.test_app_01_5_home_chat_deterministic import _seed_datos


def _seed_recetas_contexto(core: HostAICore) -> None:
    _seed_datos(core)
    repo = RepositorioBibliotecaRecetas601(core.base_dir)
    for idx in range(1, 4):
        repo.crear(
            {
                "nombre": f"Paella Contexto {idx}",
                "numero_raciones": 4,
                "ingredientes": ["Arroz"],
                "cantidades": ["0.5 kg"],
                "elaboracion": "Proceso de prueba",
            }
        )


def test_buscar_receta_guarda_contexto_de_lista(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    _seed_recetas_contexto(shell.core)

    r = shell.chat.enviar("busca receta paella")
    sesion = shell.chat.estado_sesion()

    assert r["ok"] is True
    assert r["datos"]["intent"]["intent"] == "BUSCAR_RECETA"
    assert len(sesion.get("ultima_lista_mostrada") or []) >= 3
    assert sesion.get("ultima_busqueda") == "paella"


def test_abrir_primera_segunda_ultima_desde_contexto(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    _seed_recetas_contexto(shell.core)

    base = shell.chat.enviar("busca receta paella")
    resultados = list((base.get("datos") or {}).get("resultados") or [])

    r1 = shell.chat.enviar("abre la primera")
    r2 = shell.chat.enviar("abre la segunda")
    r3 = shell.chat.enviar("abre la ultima")

    nav1 = dict((r1.get("datos") or {}).get("navigation_request") or {})
    nav2 = dict((r2.get("datos") or {}).get("navigation_request") or {})
    nav3 = dict((r3.get("datos") or {}).get("navigation_request") or {})

    assert nav1.get("entity_id") == str(resultados[0].get("id") or resultados[0].get("codigo") or "")
    assert nav2.get("entity_id") == str(resultados[1].get("id") or resultados[1].get("codigo") or "")
    assert nav3.get("entity_id") == str(resultados[-1].get("id") or resultados[-1].get("codigo") or "")


def test_contexto_inexistente_y_ambiguo(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))

    r1 = shell.chat.enviar("abre la primera")
    r2 = shell.chat.enviar("muestra el escandallo")

    assert r1["tipo_mensaje"] == "ADVERTENCIA"
    assert "lista activa" in r1["mensaje"].lower()
    assert r2["tipo_mensaje"] == "ADVERTENCIA"
    assert "no tengo una receta" in r2["mensaje"].lower()


def test_abrir_escandallo_y_menu_con_contexto_activo(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    _seed_recetas_contexto(shell.core)

    base = shell.chat.enviar("busca receta paella")
    resultados = list((base.get("datos") or {}).get("resultados") or [])
    r_ref = shell.chat.enviar("abre la primera")
    nav_ref = dict((r_ref.get("datos") or {}).get("navigation_request") or {})
    shell.chat.aplicar_navigation_request(nav_ref)

    r_esc = shell.chat.enviar("muestra el escandallo")
    r_menu = shell.chat.enviar("muestra el menu")

    nav_esc = dict((r_esc.get("datos") or {}).get("navigation_request") or {})
    nav_menu = dict((r_menu.get("datos") or {}).get("navigation_request") or {})

    assert len(resultados) >= 1
    assert nav_esc.get("target_module") == "RECETAS_ESCANDALLOS"
    assert nav_menu.get("target_module") == "MENUS"


def test_navigation_request_actualiza_contexto_y_shell_navega(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    llamadas: list[str] = []
    shell.app._menu_eventos = lambda: llamadas.append("eventos")

    r = shell.chat.enviar("abre eventos")
    shell._pending_navigation_request = dict((r.get("datos") or {}).get("navigation_request") or {})
    shell._procesar_navegacion_pendiente(lambda *_: None)

    sesion = shell.chat.estado_sesion()
    assert llamadas == ["eventos"]
    assert sesion.get("ultimo_modulo") == "EVENTOS"


def test_clear_limpia_contexto_sesion(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    _seed_recetas_contexto(shell.core)

    shell.chat.enviar("busca receta paella")
    shell.chat.limpiar()
    sesion = shell.chat.estado_sesion()

    assert sesion.get("contexto_activo") == "HOME"
    assert sesion.get("ultima_busqueda") == ""
    assert sesion.get("ultima_lista_mostrada") == []
    assert sesion.get("historial_corto_acciones") == []


def test_sesion_nueva_no_reutiliza_contexto(tmp_path: Path):
    shell_a = AppShellHostAI(HostAICore(tmp_path / "a"))
    _seed_recetas_contexto(shell_a.core)
    shell_a.chat.enviar("busca receta paella")

    shell_b = AppShellHostAI(HostAICore(tmp_path / "b"))
    sesion_b = shell_b.chat.estado_sesion()

    assert sesion_b.get("contexto_activo") == "HOME"
    assert sesion_b.get("ultima_lista_mostrada") == []


def test_no_persistencia_contexto_en_disco(tmp_path: Path):
    shell = AppShellHostAI(HostAICore(tmp_path))
    _seed_recetas_contexto(shell.core)
    shell.chat.enviar("busca receta paella")

    db_files = list((shell.core.base_dir / "DATOS" / "db").glob("*.json"))
    textos = "\n".join([p.read_text(encoding="utf-8", errors="ignore") for p in db_files])

    assert "historial_corto_acciones" not in textos
    assert "ultima_lista_mostrada" not in textos
