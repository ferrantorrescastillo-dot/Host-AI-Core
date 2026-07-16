from types import SimpleNamespace

from APP.consola import AppConsolaHostAI


class Contexto:
    def __init__(self, evento_id="EVT-1"):
        self.valores = {"evento_id": evento_id}

    def obtener(self, clave):
        return self.valores.get(clave)

    def establecer(self, clave, valor):
        self.valores[clave] = valor


def pase(nombre="Principal"):
    return SimpleNamespace(id="PASE-1", nombre=nombre, hora_inicio="14:30", recetas=["REC-1"], notas="")


def servicio(pases=None):
    return SimpleNamespace(
        id="SERV-1", nombre="Comida", tipo="comida", hora_inicio="14:00",
        duracion_min=120, pases=list(pases or []),
    )


def evento(servicios=None, estado="confirmado"):
    return SimpleNamespace(
        id="EVT-1", nombre="Boda profesional", fecha="2026-10-10", hora_inicio="14:00",
        pax=90, estado=estado, servicios=list(servicios or []), cliente="Ana", ubicacion="Masía",
        tipo="boda", telefono="", email="", observaciones="Sin frutos secos",
    )


def app_para(evento_actual, planes=None, compras=None):
    app = AppConsolaHostAI.__new__(AppConsolaHostAI)
    app._contexto_global = Contexto(evento_actual.id)
    app.core = SimpleNamespace(
        eventos=SimpleNamespace(
            obtener=lambda _: evento_actual,
            resumen_ejecutivo=lambda _: {
                "totales": {
                    "servicios": len(evento_actual.servicios),
                    "pases": sum(len(s.pases) for s in evento_actual.servicios),
                    "recetas": sum(len(p.recetas) for s in evento_actual.servicios for p in s.pases),
                    "recetas_unicas": 1 if any(s.pases for s in evento_actual.servicios) else 0,
                },
                "avisos": [] if evento_actual.servicios and all(s.pases for s in evento_actual.servicios) else ["Falta completar el menú."],
            },
        ),
        produccion_real=SimpleNamespace(listar_planes=lambda: list(planes or [])),
        compras=SimpleNamespace(listar_necesidades=lambda solo_pendientes=False: list(compras or [])),
    )
    return app


def test_tipo_desconocido_no_se_acepta_y_ofrece_alternativas(monkeypatch, capsys):
    respuestas = iter(["sboda", "1"])
    monkeypatch.setattr("builtins.input", lambda _: next(respuestas))

    assert AppConsolaHostAI._pedir_tipo_evento() == "boda"

    salida = capsys.readouterr().out
    assert "No reconozco 'sboda'" in salida
    assert "1. boda" in salida and "2. catering" in salida and "3. evento" in salida


def test_progreso_muestra_cinco_pasos_y_paso_activo(capsys):
    app = app_para(evento([servicio()]))

    app._mostrar_progreso_evento()

    salida = capsys.readouterr().out
    assert "Paso 3 de 5" in salida
    assert "✓ Evento" in salida
    assert "✓ Servicios" in salida
    assert "▶ Menú" in salida
    assert "□ Producción" in salida and "□ Compras" in salida


def test_despues_de_servicio_habla_como_companero(monkeypatch, capsys):
    app = app_para(evento([servicio()]))
    app._gestionar_servicios_evento_activo = lambda: None
    app._gestionar_pases_evento_activo = lambda: None
    respuestas = iter(["0"])
    monkeypatch.setattr("builtins.input", lambda _: next(respuestas))

    app._continuar_preparacion_evento("servicio")

    salida = capsys.readouterr().out
    assert "Perfecto." in salida
    assert "Ya tenemos este servicio preparado" in salida
    assert "1. Añadir otro servicio" in salida
    assert "2. Preparar el menú del evento" in salida


def test_menu_completo_conduce_a_produccion(monkeypatch, capsys):
    app = app_para(evento([servicio([pase()])]))
    preparado = []
    app._preparar_produccion_evento_activo = lambda: preparado.append(True)
    monkeypatch.setattr("builtins.input", lambda _: "1")

    app._continuar_preparacion_evento("pase")

    assert preparado == [True]
    salida = capsys.readouterr().out
    assert "El menú del evento ya está preparado" in salida
    assert "El siguiente paso es preparar la producción" in salida


def test_resumen_rapido_solo_muestra_estado_y_ofrece_detalle(monkeypatch, capsys):
    plan = {"id": "PLAN-1", "evento_id": "EVT-1", "nombre": "Plan boda", "estado": "ok"}
    app = app_para(evento([servicio([pase()])]), [plan])
    monkeypatch.setattr("builtins.input", lambda _: "0")

    app._ver_resumen_rapido_evento_activo()

    salida = capsys.readouterr().out
    assert "RESUMEN RÁPIDO" in salida
    assert "✓ Evento creado" in salida
    assert "✓ Servicios preparados" in salida
    assert "✓ Menú preparado" in salida
    assert "✓ Producción preparada" in salida
    assert "1. Ver resumen completo" in salida
    assert "SERVICIOS Y PASES" not in salida


def test_resumen_completo_usa_solo_detalle_existente(capsys):
    plan = {"id": "PLAN-1", "evento_id": "EVT-1", "nombre": "Plan boda", "estado": "ok"}
    compra = {"id": "COMP-1", "evento_id": "EVT-1", "nombre": "Verduras", "estado": "pendiente"}
    app = app_para(evento([servicio([pase()])]), [plan], [compra])

    app._ver_resumen_ejecutivo_evento_activo()

    salida = capsys.readouterr().out
    assert "SERVICIOS Y PASES" in salida and "Principal" in salida
    assert "Plan boda" in salida
    assert "Verduras" in salida
    assert "CRONOLOGÍA" in salida
    assert "Sin frutos secos" in salida


def test_evento_cancelado_no_propone_nueva_preparacion(monkeypatch, capsys):
    app = app_para(evento(estado="cancelado"))
    monkeypatch.setattr("builtins.input", lambda _: "0")

    app._continuar_preparacion_evento("seleccion")

    salida = capsys.readouterr().out
    assert "Este evento está cancelado" in salida
    assert "Preparar los servicios del evento" not in salida


def test_evento_retomado_continua_desde_produccion_existente(monkeypatch, capsys):
    plan = {"id": "PLAN-1", "evento_id": "EVT-1", "nombre": "Plan boda", "estado": "ok"}
    app = app_para(evento([servicio([pase()])]), [plan])
    abierto = []
    app._abrir_produccion_viva = lambda: abierto.append(True)
    monkeypatch.setattr("builtins.input", lambda _: "1")

    app._continuar_preparacion_evento("seleccion")

    assert abierto == [True]
    assert "1. Abrir Producción Viva" in capsys.readouterr().out
