from APP.consola import AppConsolaHostAI


class Plan:
    def __init__(self, data):
        self._data = data
    def to_dict(self):
        return dict(self._data)


class Produccion:
    def __init__(self):
        self.data = {
            "PLAN-1": {
                "id": "PLAN-1",
                "nombre": "Boda prueba RR1",
                "estado": "planificado",
                "fecha": "2026-09-20",
            }
        }
    def obtener_plan(self, plan_id):
        return Plan(self.data[plan_id])
    def listar_planes(self):
        return list(self.data.values())
    def buscar_planes(self, texto):
        q = texto.lower()
        return [p for p in self.data.values() if q in p["nombre"].lower() or q == p["id"].lower()]


class Core:
    def __init__(self):
        self.produccion_real = Produccion()


def test_rr11_reutiliza_plan_activo_sin_pedir_busqueda(monkeypatch):
    app = AppConsolaHostAI(Core())
    app.ultimo_plan_produccion_id = "PLAN-1"
    monkeypatch.setattr("builtins.input", lambda *_: (_ for _ in ()).throw(AssertionError("No debe pedir búsqueda")))
    plan = app._seleccionar_plan_produccion()
    assert plan["id"] == "PLAN-1"


def test_rr11_busqueda_tolerante_propone_plan_parecido(monkeypatch):
    app = AppConsolaHostAI(Core())
    respuestas = iter(["Boa pruena RR1"])
    monkeypatch.setattr("builtins.input", lambda *_: next(respuestas))
    plan = app._seleccionar_plan_produccion(usar_activo=False)
    assert plan["id"] == "PLAN-1"
    assert app.ultimo_plan_produccion_id == "PLAN-1"


def test_rr11_hora_desde_minutos():
    assert AppConsolaHostAI._hora_desde_minutos(0, "08:00") == "08:00"
    assert AppConsolaHostAI._hora_desde_minutos(355, "08:00") == "13:55"
