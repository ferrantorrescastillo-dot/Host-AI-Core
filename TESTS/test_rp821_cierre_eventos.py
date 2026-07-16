from datetime import date
from types import SimpleNamespace

from APP.consola import AppConsolaHostAI


class Contexto:
    def __init__(self, evento_id=None):
        self.valores = {"evento_id": evento_id}

    def obtener(self, clave):
        return self.valores.get(clave)

    def establecer(self, clave, valor):
        self.valores[clave] = valor


def pase():
    return SimpleNamespace(nombre="Principal", hora_inicio="14:30", recetas=["REC-1"], notas="")


def servicio(pases=None):
    return SimpleNamespace(nombre="Comida", hora_inicio="14:00", pases=list(pases or []))


def evento(nombre="Boda Ana", estado="confirmado", servicios=None, fecha="2026-10-10"):
    return SimpleNamespace(
        id=f"EVT-{nombre}", nombre=nombre, fecha=fecha, hora_inicio="14:00", pax=90,
        estado=estado, servicios=list(servicios or []), observaciones="",
    )


def crear_app(eventos, planes=None):
    app = AppConsolaHostAI.__new__(AppConsolaHostAI)
    por_id = {e.id: e for e in eventos}
    app._contexto_global = Contexto(eventos[0].id if eventos else None)
    app.core = SimpleNamespace(
        eventos=SimpleNamespace(
            listar_eventos=lambda: list(eventos),
            obtener=lambda evento_id: por_id[evento_id],
        ),
        produccion_real=SimpleNamespace(listar_planes=lambda: list(planes or [])),
    )
    return app


def test_entrada_siempre_pregunta_antes_de_abrir_evento(monkeypatch, capsys):
    app = crear_app([evento()])
    monkeypatch.setattr("builtins.input", lambda _: "0")

    app._menu_eventos()

    salida = capsys.readouterr().out
    assert "EVENTOS" in salida and "¿Qué quieres hacer?" in salida
    assert "1. Continuar preparando un evento (1 activos)" in salida
    assert "Próximo: Boda Ana · 2026-10-10 · 90 pax" in salida
    assert salida.index("Continuar preparando") < salida.index("Crear un evento nuevo")


def test_evento_futuro_se_muestra_como_proximo():
    actual = evento(nombre="Boda futura", fecha="2026-10-10")

    texto = AppConsolaHostAI._texto_evento_destacado(actual, date(2026, 7, 16))

    assert texto == "Próximo: Boda futura · 2026-10-10 · 90 pax"


def test_evento_pasado_abierto_se_senala_para_revision():
    actual = evento(nombre="Boronat", fecha="2026-07-11")

    texto = AppConsolaHostAI._texto_evento_destacado(actual, date(2026, 7, 16))

    assert texto == "⚠ Evento pasado pendiente de revisar: Boronat · 2026-07-11 · 90 pax"


def test_evento_sin_fecha_utilizable_lo_explica():
    actual = evento(nombre="Catering por confirmar", fecha="pendiente")

    texto = AppConsolaHostAI._texto_evento_destacado(actual, date(2026, 7, 16))

    assert texto == "Evento activo sin fecha confirmada: Catering por confirmar · 90 pax"


def test_entrada_sin_eventos_recomienda_crear(monkeypatch, capsys):
    app = crear_app([])
    monkeypatch.setattr("builtins.input", lambda _: "0")

    app._menu_eventos()

    salida = capsys.readouterr().out
    assert "1. Crear evento" in salida
    assert "Recomendación: empieza creando" in salida
    assert "Continuar preparando un evento" not in salida


def test_entrada_separa_calendario_finalizados_y_mas_opciones(monkeypatch, capsys):
    app = crear_app([evento()])
    monkeypatch.setattr("builtins.input", lambda _: "0")

    app._menu_eventos()

    salida = capsys.readouterr().out
    assert "4. Calendario" in salida
    assert "5. Eventos finalizados" in salida
    assert "6. Más opciones" in salida


def test_fase_servicios_muestra_solo_acciones_utiles(monkeypatch, capsys):
    app = crear_app([evento()])
    app._gestionar_servicios_evento_activo = lambda: None
    monkeypatch.setattr("builtins.input", lambda _: "0")

    app._continuar_preparacion_evento("seleccion")

    salida = capsys.readouterr().out
    assert "FASE SERVICIOS" in salida
    assert "1. Continuar preparando servicios" in salida
    assert "2. Ver resumen" in salida
    assert "3. Cambiar de fase" in salida
    assert "4. Más opciones" in salida
    assert "Abrir Producción Viva" not in salida
    assert "Ver cronología" not in salida


def test_fase_menu_prioriza_menu_y_revisar_servicios(monkeypatch, capsys):
    app = crear_app([evento(servicios=[servicio()])])
    monkeypatch.setattr("builtins.input", lambda _: "0")

    app._continuar_preparacion_evento("seleccion")

    salida = capsys.readouterr().out
    assert "FASE MENÚ" in salida
    assert "1. Continuar preparando el menú" in salida
    assert "3. Revisar servicios" in salida
    assert "Abrir Producción Viva" not in salida


def test_menu_terminado_no_muestra_produccion_inexistente_como_opcion(monkeypatch, capsys):
    app = crear_app([evento(servicios=[servicio([pase()])])])
    monkeypatch.setattr("builtins.input", lambda _: "0")

    app._continuar_preparacion_evento("seleccion")

    salida = capsys.readouterr().out
    assert "MENÚ PREPARADO" in salida
    assert "1. Continuar con el siguiente paso" in salida
    assert "Abrir Producción Viva" not in salida


def test_fase_produccion_solo_muestra_produccion_si_existe(monkeypatch, capsys):
    actual = evento(servicios=[servicio([pase()])])
    plan = {"id": "PLAN-1", "evento_id": actual.id, "nombre": "Plan boda"}
    app = crear_app([actual], [plan])
    monkeypatch.setattr("builtins.input", lambda _: "0")

    app._continuar_preparacion_evento("seleccion")

    salida = capsys.readouterr().out
    assert "FASE PRODUCCIÓN" in salida
    assert "1. Abrir Producción Viva" in salida
    assert "3. Revisar menú" in salida
    assert "Abrir ficha completa" not in salida


def test_mas_opciones_agrupa_cronologia_ficha_y_avanzadas(monkeypatch, capsys):
    app = crear_app([evento()])
    monkeypatch.setattr("builtins.input", lambda _: "0")

    app._mas_opciones_evento()

    salida = capsys.readouterr().out
    assert "Ver cronología" in salida
    assert "Editar datos del evento" in salida
    assert "Abrir ficha completa" in salida
    assert "Acciones avanzadas" in salida
