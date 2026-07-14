from pathlib import Path
import sys
from datetime import date

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI


def preparar_escandallo(core):
    esc = core.orquestador.resolver(SolicitudHostAI("registrar_escandallo", {
        "receta_id": "REC-CARRILLERA",
        "nombre": "Carrillera melosa",
        "raciones_base": 10,
        "grupo": "Carnes",
        "lineas": [
            {
                "nombre": "Carrillera de ternera",
                "cantidad": 1.8,
                "unidad": "kg",
                "tipo": "articulo",
                "articulo_id": "ART-CARRILLERA",
                "merma_porcentaje": 10,
                "familia": "carnes",
                "proveedor_preferente": "Proveedor Carnes",
                "coste_unitario": 8.5
            },
            {
                "nombre": "Demi-glace",
                "cantidad": 0.8,
                "unidad": "L",
                "tipo": "elaboracion",
                "elaboracion_id": "ELAB-DEMI",
                "merma_porcentaje": 0,
                "familia": "salsas",
                "proveedor_preferente": "Producción interna",
                "coste_unitario": 3.0
            }
        ]
    }))
    assert esc.ok is True


def crear_evento(core):
    ev = core.orquestador.resolver(SolicitudHostAI("crear_evento", {
        "nombre": "Boda producción real",
        "fecha": date.today().isoformat(),
        "pax": 80,
        "tipo": "boda",
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
        "recetas": ["REC-CARRILLERA"],
    }))
    assert pase.ok is True
    return evento_id


def ejecutar_prueba():
    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "produccion_real" for p in listado.datos["pipelines"])

    preparar_escandallo(core)
    evento_id = crear_evento(core)

    plan = core.orquestador.resolver(SolicitudHostAI("planificar_produccion_real_evento", {
        "evento_id": evento_id,
        "hora_inicio": "08:00",
        "equipo_cocina": 2,
        "incluir_logistica": True,
    }))
    assert plan.ok is True
    assert plan.datos["evento"] == "Boda producción real"
    assert len(plan.datos["tareas"]) >= 3
    assert len(plan.datos["cronograma"]) >= 8
    assert plan.datos["duracion_total_min"] > 0
    plan_id = plan.datos["id"]

    tipos = {b["tipo"] for b in plan.datos["cronograma"]}
    assert "preparacion" in tipos
    assert "coccion" in tipos or "produccion" in tipos
    assert "logistica" in tipos

    diag = core.orquestador.resolver(SolicitudHostAI("diagnosticar_plan_produccion_real", {
        "plan_id": plan_id,
    }))
    assert diag.ok is True
    assert "duracion_total_min" in diag.datos
    assert "recursos_usados" in diag.datos

    reparto = core.orquestador.resolver(SolicitudHostAI("repartir_trabajo_produccion_real", {
        "plan_id": plan_id,
    }))
    assert reparto.ok is True
    assert len(reparto.datos["reparto"]) >= 1

    listado_planes = core.orquestador.resolver(SolicitudHostAI("listar_planes_produccion_real", {}))
    assert listado_planes.ok is True
    assert len(listado_planes.datos["planes"]) >= 1

    print("TEST OK - Host AI v2.0.7 Motor de Producción Real")
    print("Plan:", plan.to_dict())
    print("Diagnóstico:", diag.to_dict())
    print("Reparto:", reparto.to_dict())


if __name__ == "__main__":
    ejecutar_prueba()
