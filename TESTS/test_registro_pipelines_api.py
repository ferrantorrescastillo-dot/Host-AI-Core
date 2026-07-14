from pathlib import Path
import sys
from datetime import date

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI


def ejecutar_prueba():
    core = HostAICore(BASE_DIR)
    if hasattr(core, "memoria"):
        core.memoria.limpiar_memoria()

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "evento" for p in listado.datos["pipelines"])

    crear = core.orquestador.resolver(SolicitudHostAI("ejecutar_pipeline", {
        "pipeline": "evento",
        "accion": "crear",
        "parametros": {
            "nombre": "Evento API interna",
            "fecha": date.today().isoformat(),
            "pax": 80,
            "tipo": "catering",
            "cliente": "Cliente Demo",
            "ubicacion": "Finca Demo",
        }
    }))
    assert crear.ok is True
    evento_id = crear.datos["resultado_pipeline"]["datos"]["evento"]["id"]

    servicio = core.orquestador.resolver(SolicitudHostAI("ejecutar_pipeline", {
        "pipeline": "evento",
        "accion": "agregar_servicio",
        "parametros": {
            "evento_id": evento_id,
            "nombre": "Cena",
            "tipo": "cena",
            "hora_inicio": "20:00",
            "duracion_min": 180,
        }
    }))
    assert servicio.ok is True
    servicio_id = servicio.datos["resultado_pipeline"]["datos"]["evento"]["servicios"][0]["id"]

    pase = core.orquestador.resolver(SolicitudHostAI("ejecutar_pipeline", {
        "pipeline": "evento",
        "accion": "agregar_pase",
        "parametros": {
            "evento_id": evento_id,
            "servicio_id": servicio_id,
            "nombre": "Principal",
            "hora_inicio": "21:00",
            "duracion_min": 35,
            "recetas": ["REC-CARRILLERA"],
        }
    }))
    assert pase.ok is True

    organizar = core.orquestador.resolver(SolicitudHostAI("organizar_evento_director_api", {
        "evento_id": evento_id,
        "hora_inicio_produccion": "08:00",
    }))
    assert organizar.ok is True
    assert "linea_temporal" in organizar.datos
    assert "diagnostico" in organizar.datos
    assert "simulacion_produccion" in organizar.datos

    malo = core.orquestador.resolver(SolicitudHostAI("ejecutar_pipeline", {
        "pipeline": "no_existe",
        "accion": "crear",
        "parametros": {}
    }))
    assert malo.ok is False

    print("TEST OK - Host AI v1.0.1 Registro de Pipelines y API Interna")
    print("Pipelines:", listado.to_dict())
    print("Organizar evento:", organizar.to_dict())


if __name__ == "__main__":
    ejecutar_prueba()
