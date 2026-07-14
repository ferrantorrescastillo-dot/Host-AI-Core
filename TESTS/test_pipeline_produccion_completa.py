from pathlib import Path
import sys
from datetime import date, timedelta

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def crear_evento(core):
    ev = core.orquestador.resolver(SolicitudHostAI("crear_evento", {
        "nombre": "Evento producción completa",
        "fecha": date.today().isoformat(),
        "pax": 80,
        "tipo": "catering",
        "cliente": "Cliente Demo",
        "ubicacion": "Finca Demo",
    }))
    assert ev.ok is True
    evento_id = ev.datos["evento"]["id"]
    serv = core.orquestador.resolver(SolicitudHostAI("agregar_servicio_evento", {
        "evento_id": evento_id,
        "nombre": "Cena",
        "tipo": "cena",
        "hora_inicio": "20:00",
        "duracion_min": 180,
    }))
    assert serv.ok is True
    servicio_id = serv.datos["evento"]["servicios"][0]["id"]
    pase = core.orquestador.resolver(SolicitudHostAI("agregar_pase_evento", {
        "evento_id": evento_id,
        "servicio_id": servicio_id,
        "nombre": "Principal",
        "hora_inicio": "21:00",
        "duracion_min": 35,
        "recetas": ["REC-CARRILLERA", "REC-DEMI-GLACE"],
    }))
    assert pase.ok is True
    return evento_id

def ejecutar_prueba():
    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "produccion_completa" for p in listado.datos["pipelines"])

    entrada = core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {
        "nombre": "Carrillera",
        "cantidad": 3,
        "unidad": "ud",
        "familia": "produccion_evento",
        "ubicacion": "Cámara 1",
        "caducidad": (date.today() + timedelta(days=3)).isoformat(),
        "articulo_id": "REC-CARRILLERA",
    }))
    assert entrada.ok is True

    evento_id = crear_evento(core)

    informe = core.orquestador.resolver(SolicitudHostAI("analizar_produccion_completa_evento", {
        "evento_id": evento_id,
        "hora_inicio_produccion": "08:00",
        "margen_seguridad_min": 60,
        "generar_compras": True,
    }))
    assert informe.ok is True
    assert informe.requiere_aprobacion is True
    assert informe.datos["evento"] == "Evento producción completa"
    assert len(informe.datos["necesidades"]) == 2
    assert len(informe.datos["predicciones_stock"]) == 2
    assert len(informe.datos["compras_generadas"]) >= 1
    assert informe.datos["estado"] == "revisar"

    pedidos = core.orquestador.resolver(SolicitudHostAI("generar_pedidos_desde_evento", {
        "evento_id": evento_id,
    }))
    assert pedidos.ok is True
    assert pedidos.requiere_aprobacion is True
    assert pedidos.datos["total_necesidades"] >= 1

    informes = core.orquestador.resolver(SolicitudHostAI("listar_informes_produccion_completa", {}))
    assert informes.ok is True
    assert len(informes.datos["informes"]) >= 1

    print("TEST OK - Host AI v1.0.4 Pipeline de Producción Completa Inicial")
    print("Informe:", informe.to_dict())
    print("Pedidos:", pedidos.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
