from pathlib import Path
import sys
from datetime import date

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI


def preparar_stock(core):
    for item in [
        {"nombre": "Carrillera de ternera", "cantidad": 6, "unidad": "kg", "familia": "carnes", "articulo_id": "ART-CARRILLERA"},
        {"nombre": "Demi-glace", "cantidad": 2, "unidad": "L", "familia": "salsas", "articulo_id": "ART-DEMI"},
        {"nombre": "Patata", "cantidad": 8, "unidad": "kg", "familia": "verduras", "articulo_id": "ART-PATATA"},
    ]:
        r = core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", item))
        assert r.ok is True


def ejecutar_prueba():
    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "asistente" for p in listado.datos["pipelines"])

    crear = core.orquestador.resolver(SolicitudHostAI("chat_host_ai", {
        "texto": "Tengo una boda de 80 pax",
        "contexto": {"fecha": date.today().isoformat()}
    }))
    assert crear.ok is True
    assert crear.datos["intencion"]["intencion"] == "crear_evento"
    assert crear.datos["resultado"]["ok"] is True
    evento_id = crear.datos["resultado"]["datos"]["evento"]["id"]

    preparar_stock(core)

    platos = core.orquestador.resolver(SolicitudHostAI("chat_host_ai", {
        "texto": "Hazme un plato con las sobras de stock para comida personal",
        "contexto": {"raciones": 6}
    }))
    assert platos.ok is True
    assert platos.datos["intencion"]["intencion"] == "proponer_platos_stock"
    assert len(platos.datos["resultado"]["datos"]["ideas"]) >= 1

    coste_incompleto = core.orquestador.resolver(SolicitudHostAI("chat_host_ai", {
        "texto": "Calcula cuánto cuesta el evento",
        "contexto": {}
    }))
    assert coste_incompleto.ok is True
    assert coste_incompleto.requiere_aprobacion is True
    assert coste_incompleto.datos["intencion"]["intencion"] == "calcular_coste_evento_incompleto"

    plan_incompleto = core.orquestador.resolver(SolicitudHostAI("chat_host_ai", {
        "texto": "Planifica la producción",
        "contexto": {}
    }))
    assert plan_incompleto.ok is True
    assert plan_incompleto.requiere_aprobacion is True

    detectar = core.orquestador.resolver(SolicitudHostAI("detectar_intencion_chat", {
        "texto": "Dime el stock actual"
    }))
    assert detectar.ok is True
    assert detectar.datos["intencion"]["intencion"] == "stock_actual"

    historial = core.orquestador.resolver(SolicitudHostAI("historial_chat", {}))
    assert historial.ok is True
    assert historial.datos["total"] >= 4

    print("TEST OK - Host AI v2.0.9 Asistente Conversacional Inicial")
    print("Crear evento:", crear.to_dict())
    print("Platos:", platos.to_dict())
    print("Historial:", historial.to_dict())


if __name__ == "__main__":
    ejecutar_prueba()
