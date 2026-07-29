from __future__ import annotations

from pathlib import Path
import json

from SERVICIOS.auditor_arranque_piloto_01 import AuditorArranquePiloto01
from SERVICIOS.certificador_piloto_01 import CertificadorPiloto01
from SERVICIOS.configuracion_piloto_01 import ConfiguracionPiloto01
from SERVICIOS.inventario_modulos_piloto_01 import InventarioModulosPiloto01
from SERVICIOS.lanzador_piloto_01 import LanzadorPiloto01
from APP.consola_piloto_01 import ConsolaPiloto01


BASE_DIR = Path(__file__).resolve().parents[1]


def test_piloto_01_configuracion_resuelve_rutas():
    resultado = ConfiguracionPiloto01(BASE_DIR).validar()
    assert resultado["ok"] is True
    assert Path(resultado["rutas"]["datos"]).is_absolute()


def test_piloto_01_inventario_clasifica_modulos():
    inventario = InventarioModulosPiloto01(BASE_DIR).generar()
    assert inventario["total_python"] > 100
    assert inventario["resumen"].get("ACTIVO", 0) > 0
    assert inventario["resumen"].get("LEGACY", 0) > 0


def test_piloto_01_auditoria_arranque_sin_errores():
    resultado = AuditorArranquePiloto01(BASE_DIR).ejecutar(importar_modulos=True)
    assert resultado["ok"] is True, resultado
    assert resultado["estado"] == "LISTO_PARA_PILOTO"


def test_piloto_01_certificador_no_modifica_negocio(tmp_path):
    resultado = CertificadorPiloto01(BASE_DIR).ejecutar(guardar_informe=False)
    assert resultado["estado"] == "CERTIFICADO"
    assert resultado["solo_lectura"] is True
    assert resultado["archivos_negocio_modificados"] == 0


def test_piloto_01_menu_separa_piloto_y_desarrollo():
    salidas: list[str] = []
    entradas = iter(["0"])
    LanzadorPiloto01(BASE_DIR).ejecutar(
        input_fn=lambda _prompt: next(entradas),
        print_fn=lambda *args: salidas.append(" ".join(map(str, args))),
    )
    texto = "\n".join(salidas)
    assert "Modo Piloto privado" in texto
    assert "Modo Desarrollo" in texto
    assert "Certificar PILOTO-0.1" in texto


def test_piloto_01_main_apunta_al_lanzador_oficial():
    contenido = (BASE_DIR / "main.py").read_text(encoding="utf-8")
    assert "lanzador_piloto_01" in contenido
    assert "ejecutar_piloto_01" in contenido


def test_piloto_privado_muestra_escandallos_recetas(capsys):
    ConsolaPiloto01._menu()
    texto = capsys.readouterr().out
    assert "1. Host AI App Shell (APP-01)" in texto
    assert "11. Escandallos y recetas" in texto


def test_piloto_privado_escandallos_recetas_reutiliza_modulo_y_vuelve(monkeypatch, capsys):
    llamadas = {"escandallos_recetas": 0}

    class _CoreDummy:
        def __init__(self):
            self.base_dir = BASE_DIR

    class _AppDummy:
        def __init__(self, core):
            self.core = core

        def _menu_escandallos_recetas(self):
            llamadas["escandallos_recetas"] += 1

    import APP.consola_piloto_01 as modulo_piloto

    monkeypatch.setattr(modulo_piloto, "AppConsolaHostAI", _AppDummy)
    entradas = iter(["11", "0"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(entradas))

    ConsolaPiloto01(_CoreDummy()).ejecutar()

    salida = capsys.readouterr().out
    assert llamadas["escandallos_recetas"] == 1
    assert salida.count("MODO PILOTO") >= 2


def test_piloto_privado_app_shell_visible_y_ejecutable(monkeypatch, capsys):
    llamadas = {"shell": 0}

    class _CoreDummy:
        def __init__(self):
            self.base_dir = BASE_DIR

    class _AppDummy:
        def __init__(self, core):
            self.core = core

    class _ShellDummy:
        def __init__(self, core, app=None):
            self.core = core
            self.app = app

        def ejecutar(self):
            llamadas["shell"] += 1

    import APP.consola_piloto_01 as modulo_piloto

    monkeypatch.setattr(modulo_piloto, "AppConsolaHostAI", _AppDummy)
    monkeypatch.setattr("APP.app_shell_host_ai.AppShellHostAI", _ShellDummy)

    entradas = iter(["1", "0"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(entradas))

    ConsolaPiloto01(_CoreDummy()).ejecutar()

    salida = capsys.readouterr().out
    assert llamadas["shell"] == 1
    assert "1. Host AI App Shell (APP-01)" in salida


def test_piloto_privado_reutiliza_mismo_punto_de_entrada_601():
    contenido_piloto = (BASE_DIR / "APP" / "consola_piloto_01.py").read_text(encoding="utf-8")
    contenido_base = (BASE_DIR / "APP" / "consola.py").read_text(encoding="utf-8")

    assert "self.app._menu_escandallos_recetas()" in contenido_piloto
    assert "def _menu_escandallos_recetas" in contenido_base
    assert "ModuloEscandallosRecetas601" in contenido_base
