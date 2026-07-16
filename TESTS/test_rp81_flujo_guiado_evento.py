from types import SimpleNamespace

from APP.consola import AppConsolaHostAI
class ContextoMemoria:
    def __init__(self, evento_id="EVT-1"):
        self.valores = {"evento_id": evento_id}

    def obtener(self, clave):
        return self.valores.get(clave)

    def establecer(self, clave, valor):
        self.valores[clave] = valor


class ProduccionFake:
    def __init__(self, planes=None):
        self.planes = list(planes or [])

    def listar_planes(self):
        return list(self.planes)


def evento(servicios=None):
    return SimpleNamespace(
        id="EVT-1", nombre="Boda guiada", fecha="2026-10-10", hora_inicio="14:00",
        pax=90, estado="confirmado", servicios=list(servicios or []),
    )


def servicio(pases=None):
    return SimpleNamespace(id="SERV-1", nombre="Comida", hora_inicio="14:00", pases=list(pases or []))


def pase():
    return SimpleNamespace(id="PASE-1", nombre="Principal", recetas=["REC-1"])


def crear_app(evento_actual, planes=None):
    app = AppConsolaHostAI.__new__(AppConsolaHostAI)
    app._contexto_global = ContextoMemoria(evento_actual.id)
    app.core = SimpleNamespace(
        eventos=SimpleNamespace(obtener=lambda _: evento_actual),
        produccion_real=ProduccionFake(planes),
    )
    return app


def test_evento_sin_servicios_propone_prepararlos(monkeypatch, capsys):
    app = crear_app(evento())
    llamado = []
    app._gestionar_servicios_evento_activo = lambda: llamado.append("servicios")
    monkeypatch.setattr("builtins.input", lambda _: "1")

    app._continuar_preparacion_evento("evento")

    assert llamado == ["servicios"]
    assert "todavía no tiene servicios" in capsys.readouterr().out


def test_evento_con_servicio_continua_por_pases(monkeypatch, capsys):
    app = crear_app(evento([servicio()]))
    llamado = []
    app._gestionar_pases_evento_activo = lambda: llamado.append("pases")
    monkeypatch.setattr("builtins.input", lambda _: "2")

    app._continuar_preparacion_evento("servicio")

    assert llamado == ["pases"]
    assert "Ahora falta preparar sus pases" in capsys.readouterr().out


def test_evento_con_pases_continua_por_produccion(monkeypatch, capsys):
    app = crear_app(evento([servicio([pase()])]))
    llamado = []
    app._preparar_produccion_evento_activo = lambda: llamado.append("produccion")
    monkeypatch.setattr("builtins.input", lambda _: "1")

    app._continuar_preparacion_evento("pase")

    assert llamado == ["produccion"]
    assert "El siguiente paso es preparar la producción" in capsys.readouterr().out


def test_evento_con_produccion_abre_produccion_viva(monkeypatch, capsys):
    plan = {"id": "PLAN-1", "evento_id": "EVT-1", "nombre": "Producción boda"}
    app = crear_app(evento([servicio([pase()])]), [plan])
    llamado = []
    app._abrir_produccion_viva = lambda: llamado.append("viva")
    monkeypatch.setattr("builtins.input", lambda _: "1")

    app._continuar_preparacion_evento("produccion")

    assert llamado == ["viva"]
    assert "ya tiene producción preparada" in capsys.readouterr().out


def test_planes_se_detectan_por_identificador_del_evento():
    planes = [
        {"id": "OTRO", "evento_id": "EVT-2"},
        {"id": "PLAN-1", "evento_id": "EVT-1"},
    ]
    app = crear_app(evento([servicio([pase()])]), planes)

    assert [p["id"] for p in app._planes_del_evento_activo()] == ["PLAN-1"]


def test_produccion_creada_pregunta_y_abre_produccion_viva(monkeypatch, capsys):
    evento_actual = evento([servicio([pase()])])
    app = crear_app(evento_actual)
    app.core.orquestador = SimpleNamespace(resolver=lambda solicitud: SimpleNamespace(
        ok=True, mensaje="Producción creada.", datos={"id": "PLAN-1", "evento": evento_actual.nombre}
    ))
    abierto = []
    app._abrir_produccion_viva = lambda: abierto.append(True)
    respuestas = iter(["07:30", "3", "s"])
    monkeypatch.setattr("builtins.input", lambda _: next(respuestas))

    resultado = app._preparar_produccion_evento_activo()

    assert resultado["id"] == "PLAN-1"
    assert app.ultimo_plan_produccion_id == "PLAN-1"
    assert abierto == [True]
    salida = capsys.readouterr().out
    assert "PRODUCCIÓN PREPARADA" in salida
    assert "¿Quieres abrir Producción Viva?" not in salida  # La pregunta se emite mediante input.


def test_produccion_existente_no_se_vuelve_a_generar_como_primer_paso(monkeypatch, capsys):
    plan = {"id": "PLAN-1", "evento_id": "EVT-1", "nombre": "Producción boda"}
    app = crear_app(evento([servicio([pase()])]), [plan])
    app._abrir_produccion_viva = lambda: None
    monkeypatch.setattr("builtins.input", lambda _: "0")

    app._continuar_preparacion_evento("seleccion")

    salida = capsys.readouterr().out
    assert "1. Abrir Producción Viva" in salida
    assert "1. Preparar la producción" not in salida
