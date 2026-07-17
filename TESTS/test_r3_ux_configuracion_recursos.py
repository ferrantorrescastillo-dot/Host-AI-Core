from __future__ import annotations

from types import SimpleNamespace

from APP.consola_produccion_guiada_piloto_13 import ConsolaProduccionGuiadaPiloto13


class _CfgSrv:
    def __init__(self, cfg):
        self._cfg = cfg

    def obtener_configuracion(self):
        return self._cfg


def _input_seq(*values):
    data = list(values)

    def _input(_prompt=""):
        if not data:
            raise AssertionError("Sin entradas disponibles")
        return data.pop(0)

    return _input


def _build_consola():
    r1 = {
        "partidas": [
            {"id": "partida_frio", "nombre": "Frio", "activa": True},
            {"id": "partida_caliente", "nombre": "Caliente", "activa": True},
            {"id": "partida_postres", "nombre": "Postres", "activa": True},
        ],
        "equipamiento": [
            {"id": "eq_horno_rational", "nombre": "Horno Rational", "activo": True},
            {"id": "eq_freidora", "nombre": "Freidora", "activo": True},
            {"id": "eq_plancha", "nombre": "Plancha", "activo": True},
            {"id": "eq_cocina", "nombre": "Cocina", "activo": True},
            {"id": "eq_abatidor", "nombre": "Abatidor", "activo": True},
            {"id": "eq_camara_positiva", "nombre": "Camara positiva", "activo": True},
            {"id": "eq_camara_negativa", "nombre": "Camara negativa", "activo": True},
            {"id": "eq_thermomix", "nombre": "Thermomix", "activo": True},
        ],
    }
    r2 = {
        "turnos": [
            {"id": "turno_manana", "nombre": "Manana", "activo": True},
            {"id": "turno_partido", "nombre": "Partido", "activo": True},
            {"id": "turno_tarde", "nombre": "Tarde", "activo": True},
        ],
        "personal": [
            {"id": "persona_ana", "nombre": "Ana", "activo": True},
            {"id": "persona_luis", "nombre": "Luis", "activo": True},
        ],
    }
    consola = ConsolaProduccionGuiadaPiloto13.__new__(ConsolaProduccionGuiadaPiloto13)
    consola.service = SimpleNamespace(
        produccion_recursos_reales=SimpleNamespace(
            srv_r1=_CfgSrv(r1),
            srv_r2=_CfgSrv(r2),
        )
    )
    return consola


def test_01_conversion_numero_a_id_en_requisitos():
    consola = _build_consola()
    tarea = {"requisitos_recursos": {}}
    entrada = _input_seq("2", "2,5,8", "2", "1", "45")
    out = consola._leer_requisitos_recursos(entrada, lambda *_: None, tarea)
    assert out["partida_id"] == "partida_caliente"
    assert out["equipamiento_ids"] == ["eq_freidora", "eq_abatidor", "eq_thermomix"]
    assert out["personas_necesarias"] == 2
    assert out["turno_id"] == "turno_manana"
    assert out["duracion_minutos"] == 45


def test_02_equipamiento_dedup_y_orden_mostrado():
    catalogo = [
        {"id": "eq_1", "nombre": "Uno"},
        {"id": "eq_2", "nombre": "Dos"},
        {"id": "eq_3", "nombre": "Tres"},
        {"id": "eq_4", "nombre": "Cuatro"},
        {"id": "eq_5", "nombre": "Cinco"},
    ]
    out = ConsolaProduccionGuiadaPiloto13._seleccionar_varios(
        "EQUIPAMIENTO DISPONIBLE",
        catalogo,
        "Ninguno",
        "Selecciona: ",
        _input_seq("5,2,2,1"),
        lambda *_: None,
        actual_ids=[],
    )
    assert out == ["eq_1", "eq_2", "eq_5"]


def test_03_equipamiento_rechaza_numeros_inexistentes():
    mensajes: list[str] = []
    catalogo = [
        {"id": "eq_1", "nombre": "Uno"},
        {"id": "eq_2", "nombre": "Dos"},
        {"id": "eq_3", "nombre": "Tres"},
    ]
    out = ConsolaProduccionGuiadaPiloto13._seleccionar_varios(
        "EQUIPAMIENTO DISPONIBLE",
        catalogo,
        "Ninguno",
        "Selecciona: ",
        _input_seq("9", "1,3"),
        mensajes.append,
        actual_ids=[],
    )
    assert out == ["eq_1", "eq_3"]
    assert any("Selección no válida." in m for m in mensajes)


def test_04_visualizacion_recursos_muestra_nombres_no_ids():
    tarea = {
        "requisitos_recursos": {
            "partida_id": "partida_caliente",
            "equipamiento_ids": ["eq_horno_rational", "eq_freidora"],
            "personas_necesarias": 2,
            "turno_id": "turno_manana",
            "duracion_minutos": 45,
        },
        "recursos_nombres_partida": {"partida_caliente": "Caliente"},
        "recursos_nombres_equipamiento": {
            "eq_horno_rational": "Horno Rational",
            "eq_freidora": "Freidora",
        },
        "recursos_nombres_turno": {"turno_manana": "Manana"},
    }
    lineas = ConsolaProduccionGuiadaPiloto13._resumen_recursos_tarea(tarea)
    texto = "\n".join(lineas)
    assert "Caliente" in texto
    assert "Horno Rational, Freidora" in texto
    assert "Manana" in texto
    assert "partida_caliente" not in texto
    assert "eq_horno_rational" not in texto


def test_05_edicion_muestra_valor_actual_por_nombre():
    consola = _build_consola()
    mensajes: list[str] = []
    tarea = {
        "requisitos_recursos": {
            "partida_id": "partida_caliente",
            "equipamiento_ids": ["eq_horno_rational", "eq_freidora"],
            "personas_necesarias": 2,
            "turno_id": "turno_manana",
            "duracion_minutos": 45,
        }
    }
    # Mantener valores actuales en edición.
    entrada = _input_seq("", "", "", "", "")
    out = consola._leer_requisitos_recursos(entrada, mensajes.append, tarea)
    texto = "\n".join(mensajes)
    assert "Partida actual:" in texto
    assert "Caliente" in texto
    assert "Equipamiento actual:" in texto
    assert "Horno Rational, Freidora" in texto
    assert "partida_caliente" not in texto
    assert "eq_horno_rational" not in texto
    assert out["partida_id"] == "partida_caliente"
    assert out["equipamiento_ids"] == ["eq_horno_rational", "eq_freidora"]
