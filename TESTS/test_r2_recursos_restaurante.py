from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

from APP.consola_configuracion_restaurante import ConsolaConfiguracionRestaurante
from SERVICIOS.configuracion_restaurante import ServicioConfiguracionRestaurante
from SERVICIOS.recursos_restaurante import ServicioRecursosRestaurante


def _base(tmp_path: Path) -> tuple[ServicioConfiguracionRestaurante, ServicioRecursosRestaurante]:
    s_r1 = ServicioConfiguracionRestaurante(tmp_path)
    s_r1.obtener_configuracion()
    s_r2 = ServicioRecursosRestaurante(tmp_path)
    s_r2.obtener_configuracion()
    return s_r1, s_r2


def test_01_persona_una_sola_partida(tmp_path: Path):
    _, servicio = _base(tmp_path)
    cfg = servicio.obtener_configuracion()
    cfg["personal"].append(
        {
            "nombre": "Juan Perez",
            "rol": "rol_cocinero",
            "partidas": ["partida_frio"],
            "activo": True,
        }
    )
    out = servicio.guardar_configuracion(cfg)
    assert out["personal"][0]["partidas"] == ["partida_frio"]


def test_02_persona_varias_partidas(tmp_path: Path):
    _, servicio = _base(tmp_path)
    cfg = servicio.obtener_configuracion()
    cfg["personal"].append(
        {
            "nombre": "Luis",
            "rol": "rol_ayudante",
            "partidas": ["partida_frio", "partida_caliente"],
            "activo": True,
        }
    )
    out = servicio.guardar_configuracion(cfg)
    assert out["personal"][0]["partidas"] == ["partida_frio", "partida_caliente"]


def test_03_seleccion_todas_las_partidas(tmp_path: Path):
    _base(tmp_path)
    consola = ConsolaConfiguracionRestaurante(tmp_path)
    with patch("builtins.input", side_effect=["A"]):
        seleccion = consola._seleccionar_partidas_multiples()
    assert seleccion == ["partida_frio", "partida_caliente", "partida_postres"]


def test_04_seleccion_con_espacios(tmp_path: Path):
    _base(tmp_path)
    consola = ConsolaConfiguracionRestaurante(tmp_path)
    with patch("builtins.input", side_effect=["1, 2"]):
        seleccion = consola._seleccionar_partidas_multiples()
    assert seleccion == ["partida_frio", "partida_caliente"]


def test_05_selecciones_repetidas(tmp_path: Path):
    _base(tmp_path)
    consola = ConsolaConfiguracionRestaurante(tmp_path)
    with patch("builtins.input", side_effect=["1,1,2"]):
        seleccion = consola._seleccionar_partidas_multiples()
    assert seleccion == ["partida_frio", "partida_caliente"]


def test_06_rechazo_seleccion_vacia(tmp_path: Path):
    _base(tmp_path)
    consola = ConsolaConfiguracionRestaurante(tmp_path)
    with patch("builtins.input", side_effect=[""]):
        seleccion = consola._seleccionar_partidas_multiples()
    assert seleccion is None


def test_07_rechazo_partida_inexistente(tmp_path: Path):
    _base(tmp_path)
    consola = ConsolaConfiguracionRestaurante(tmp_path)
    with patch("builtins.input", side_effect=["9"]):
        seleccion = consola._seleccionar_partidas_multiples()
    assert seleccion is None


def test_08_persistencia_multiples_partidas(tmp_path: Path):
    _, servicio = _base(tmp_path)
    cfg = servicio.obtener_configuracion()
    cfg["personal"].append(
        {
            "nombre": "Marta",
            "rol": "rol_pastelero",
            "partidas": ["partida_postres", "partida_frio"],
            "activo": True,
        }
    )
    servicio.guardar_configuracion(cfg)
    recarga = ServicioRecursosRestaurante(tmp_path).obtener_configuracion()
    assert recarga["personal"][0]["partidas"] == ["partida_postres", "partida_frio"]


def test_09_edicion_multiples_partidas(tmp_path: Path):
    _, servicio = _base(tmp_path)
    cfg = servicio.obtener_configuracion()
    cfg["personal"].append(
        {
            "nombre": "Laura",
            "rol": "rol_cocinero",
            "partidas": ["partida_frio"],
            "activo": True,
        }
    )
    cfg = servicio.guardar_configuracion(cfg)
    cfg["personal"][0]["partidas"] = ["partida_caliente", "partida_postres"]
    out = servicio.guardar_configuracion(cfg)
    assert out["personal"][0]["partidas"] == ["partida_caliente", "partida_postres"]


def test_10_migracion_desde_campo_antiguo_partida(tmp_path: Path):
    _base(tmp_path)
    ruta = tmp_path / "DATOS" / "db" / "recursos_restaurante.json"
    data = json.loads(ruta.read_text(encoding="utf-8"))
    data["personal"] = [
        {
            "id": "persona_marcelo",
            "nombre": "Marcelo",
            "rol": "rol_ayudante",
            "partida": "partida_frio",
            "activo": True,
        }
    ]
    ruta.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    cfg = ServicioRecursosRestaurante(tmp_path).obtener_configuracion()
    assert cfg["personal"][0]["partidas"] == ["partida_frio"]


def test_11_guardado_solo_con_partidas(tmp_path: Path):
    _base(tmp_path)
    ruta = tmp_path / "DATOS" / "db" / "recursos_restaurante.json"
    data = json.loads(ruta.read_text(encoding="utf-8"))
    data["personal"] = [
        {
            "id": "persona_marcelo",
            "nombre": "Marcelo",
            "rol": "rol_ayudante",
            "partida": "partida_frio",
            "activo": True,
        }
    ]
    ruta.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    servicio = ServicioRecursosRestaurante(tmp_path)
    cfg = servicio.obtener_configuracion()
    servicio.guardar_configuracion(cfg)

    guardado = json.loads(ruta.read_text(encoding="utf-8"))
    assert "partidas" in guardado["personal"][0]
    assert "partida" not in guardado["personal"][0]


def test_12_impide_eliminar_partida_asignada(tmp_path: Path):
    _, servicio_r2 = _base(tmp_path)
    cfg = servicio_r2.obtener_configuracion()
    cfg["personal"] = [
        {
            "nombre": "Persona prueba",
            "rol": "rol_cocinero",
            "partidas": ["partida_frio", "partida_caliente"],
            "activo": True,
        }
    ]
    servicio_r2.guardar_configuracion(cfg)
    assert servicio_r2.esta_partida_en_uso("partida_frio") is True
    assert servicio_r2.esta_partida_en_uso("partida_postres") is False


def test_13_visualizacion_legible_multiples_partidas(tmp_path: Path):
    _base(tmp_path)
    consola = ConsolaConfiguracionRestaurante(tmp_path)
    cfg = consola.servicio_recursos.obtener_configuracion()
    cfg["personal"] = [
        {
            "nombre": "Juan Perez",
            "rol": "rol_cocinero",
            "partidas": ["partida_frio", "partida_caliente"],
            "activo": True,
        }
    ]
    consola.servicio_recursos.guardar_configuracion(cfg)

    stream = io.StringIO()
    with patch("builtins.input", side_effect=["0"]), patch("sys.stdout", stream):
        consola._menu_personal()
    out = stream.getvalue()
    assert "partidas=Frio, Caliente" in out
    assert "['partida_frio'" not in out


def test_14_compatibilidad_con_validacion_r1(tmp_path: Path):
    servicio_r1 = ServicioConfiguracionRestaurante(tmp_path)
    cfg_r1 = servicio_r1.obtener_configuracion()
    validacion = servicio_r1.validar_estructura(cfg_r1)
    assert validacion["ok"] is True
