from types import SimpleNamespace

from APP.consola import AppConsolaHostAI


class ContextoMemoria:
    def __init__(self, evento_id=None):
        self.evento_id = evento_id

    def obtener(self, clave):
        return self.evento_id if clave == "evento_id" else None

    def establecer(self, clave, valor):
        if clave == "evento_id":
            self.evento_id = valor


class EventosFake:
    ESTADOS = ("pendiente", "confirmado")

    def __init__(self, evento=None, resumen=None):
        self.evento = evento
        self.resumen = resumen or {
            "totales": {"servicios": 0, "pases": 0, "recetas": 0, "recetas_unicas": 0},
            "avisos": ["Faltan servicios."],
        }

    def obtener(self, evento_id):
        if not self.evento or self.evento.id != evento_id:
            raise ValueError(evento_id)
        return self.evento

    def resumen_ejecutivo(self, evento_id):
        return self.resumen


def crear_app(evento=None, resumen=None, planes=None, compras=None):
    app = AppConsolaHostAI.__new__(AppConsolaHostAI)
    app._contexto_global = ContextoMemoria(evento.id if evento else None)
    app.core = SimpleNamespace(
        eventos=EventosFake(evento, resumen),
        produccion_real=SimpleNamespace(listar_planes=lambda: list(planes or [])),
        compras=SimpleNamespace(listar_necesidades=lambda solo_pendientes=True: list(compras or [])),
    )
    return app


def evento_activo():
    return SimpleNamespace(
        id="EVT-1", nombre="Boda Ana", fecha="2026-09-12", hora_inicio="13:30",
        pax=120, estado="confirmado", cliente="Ana", ubicacion="Masía",
        tipo="boda", telefono="", email="", observaciones="", servicios=[],
    )


def test_menu_sin_evento_prioriza_crear_y_buscar(monkeypatch, capsys):
    app = crear_app()
    monkeypatch.setattr("builtins.input", lambda _: "0")

    app._menu_eventos()

    salida = capsys.readouterr().out
    assert salida.index("1. Crear evento") < salida.index("2. Buscar o listar eventos")
    assert "Siguiente paso" in salida
    assert "Preparar servicios" not in salida


def test_menu_con_evento_se_centra_en_continuar(monkeypatch, capsys):
    app = crear_app(evento_activo())
    monkeypatch.setattr("builtins.input", lambda _: "0")

    app._menu_eventos()

    salida = capsys.readouterr().out
    assert "EVENTO QUE ESTÁS PREPARANDO" in salida
    assert "Boda Ana" in salida and "120 pax" in salida
    assert salida.index("Ver qué falta") < salida.index("Acciones avanzadas")


def test_asistente_postalta_ofrece_continuacion(monkeypatch, capsys):
    app = crear_app(evento_activo())
    respuestas = iter(["5"])
    monkeypatch.setattr("builtins.input", lambda _: next(respuestas))

    app._continuar_tras_crear_evento()

    salida = capsys.readouterr().out
    assert "1. Añadir servicios" in salida
    assert "2. Añadir pases" in salida
    assert "3. Ver resumen" in salida
    assert "4. Abrir ficha" in salida


def test_eventos_vacios_explican_estado_y_siguiente_paso(capsys):
    AppConsolaHostAI._imprimir_eventos([])

    salida = capsys.readouterr().out
    assert "no se ha cambiado el evento activo" in salida
    assert "Siguiente paso" in salida
    assert "crea un evento" in salida


def test_servicios_vacios_proponen_primera_accion(capsys):
    app = crear_app(evento_activo())

    assert app._listar_servicios_evento_activo() == []

    salida = capsys.readouterr().out
    assert "Todavía no has preparado ningún servicio" in salida
    assert "añade el primer servicio" in salida


def test_resumen_operativo_ordena_faltas_produccion_compras_y_riesgos(capsys):
    evento = evento_activo()
    app = crear_app(evento, planes=[], compras=[])

    app._ver_resumen_ejecutivo_evento_activo()

    salida = capsys.readouterr().out
    assert salida.index("QUÉ FALTA") < salida.index("QUÉ ESTÁ LISTO")
    assert salida.index("PRODUCCIÓN QUE DEPENDE") < salida.index("COMPRAS PENDIENTES")
    assert salida.index("COMPRAS PENDIENTES") < salida.index("RIESGOS")
    assert "SIGUIENTE ACCIÓN RECOMENDADA" in salida


def test_produccion_vacia_no_es_callejon_sin_salida(capsys):
    app = crear_app(evento_activo())

    app._ver_produccion_evento_activo()

    salida = capsys.readouterr().out
    assert "producción está pendiente de generar" in salida
    assert "Estado actual" in salida
    assert "Siguiente paso" in salida
