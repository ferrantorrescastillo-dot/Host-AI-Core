from pathlib import Path
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI


def demo():
    core = HostAICore(Path(__file__).resolve().parent)
    core.memoria.limpiar_memoria()

    print("HOST AI 3.0 DEMO")
    print("-" * 50)

    r = core.orquestador.resolver(SolicitudHostAI("chat_host_ai", {
        "texto": "Tengo una boda de 80 pax",
        "contexto": {"fecha": "2026-07-07"},
    }))
    print(r.mensaje)
    evento_id = r.datos["resultado"]["datos"]["evento"]["id"]

    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {
        "nombre": "Carrillera de ternera",
        "cantidad": 6,
        "unidad": "kg",
        "familia": "carnes",
        "articulo_id": "ART-CARRILLERA",
    }))

    r = core.orquestador.resolver(SolicitudHostAI("chat_host_ai", {
        "texto": "Hazme un plato con las sobras de stock para comida personal",
        "contexto": {"raciones": 6},
    }))
    print(r.mensaje)

    r = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    print(r.mensaje)
    for p in r.datos["pipelines"]:
        print("-", p["nombre"])


if __name__ == "__main__":
    demo()
