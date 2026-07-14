from __future__ import annotations

from pathlib import Path
import json

from SERVICIOS.auditor_arranque_piloto_01 import AuditorArranquePiloto01
from SERVICIOS.certificador_piloto_01 import CertificadorPiloto01
from SERVICIOS.configuracion_piloto_01 import ConfiguracionPiloto01
from SERVICIOS.inventario_modulos_piloto_01 import InventarioModulosPiloto01
from SERVICIOS.lanzador_piloto_01 import LanzadorPiloto01


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
