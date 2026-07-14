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
                "coste_unitario": 0
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
        "nombre": "Boda coste demo",
        "fecha": date.today().isoformat(),
        "pax": 80,
        "tipo": "boda",
    }))
    evento_id = ev.datos["evento"]["id"]

    serv = core.orquestador.resolver(SolicitudHostAI("agregar_servicio_evento", {
        "evento_id": evento_id,
        "nombre": "Cena",
        "tipo": "cena",
        "hora_inicio": "20:00",
        "duracion_min": 180,
    }))
    servicio_id = serv.datos["evento"]["servicios"][0]["id"]

    core.orquestador.resolver(SolicitudHostAI("agregar_pase_evento", {
        "evento_id": evento_id,
        "servicio_id": servicio_id,
        "nombre": "Principal",
        "hora_inicio": "21:00",
        "duracion_min": 35,
        "recetas": ["REC-CARRILLERA"],
    }))
    return evento_id


def ejecutar_prueba():
    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "costes" for p in listado.datos["pipelines"])

    preparar_escandallo(core)

    p1 = core.orquestador.resolver(SolicitudHostAI("registrar_precio", {
        "nombre": "Carrillera de ternera",
        "precio_unitario": 8.5,
        "unidad": "kg",
        "articulo_id": "ART-CARRILLERA",
        "proveedor": "Proveedor Carnes",
        "familia": "carnes",
    }))
    assert p1.ok is True

    p2 = core.orquestador.resolver(SolicitudHostAI("registrar_precio", {
        "nombre": "Demi-glace",
        "precio_unitario": 3.0,
        "unidad": "L",
        "proveedor": "Producción interna",
        "familia": "salsas",
    }))
    assert p2.ok is True

    coste_receta = core.orquestador.resolver(SolicitudHostAI("calcular_coste_receta", {
        "receta_id": "REC-CARRILLERA",
        "raciones": 80,
        "precio_venta_por_racion": 18,
    }))
    assert coste_receta.ok is True
    assert round(coste_receta.datos["coste_total"], 2) == 153.84
    assert round(coste_receta.datos["coste_por_racion"], 3) == 1.923
    assert coste_receta.datos["food_cost_porcentaje"] > 0
    assert coste_receta.datos["margen_bruto"] > 0

    evento_id = crear_evento(core)

    coste_evento = core.orquestador.resolver(SolicitudHostAI("calcular_coste_evento", {
        "evento_id": evento_id,
        "precio_venta_por_pax": 45,
        "extras": [
            {"nombre": "Transporte", "cantidad": 1, "unidad": "servicio", "precio_unitario": 120, "tipo": "logistica"},
            {"nombre": "Personal extra", "cantidad": 4, "unidad": "hora", "precio_unitario": 18, "tipo": "personal"}
        ]
    }))
    assert coste_evento.ok is True
    assert coste_evento.datos["pax"] == 80
    assert coste_evento.datos["coste_total"] > coste_receta.datos["coste_total"]
    assert coste_evento.datos["precio_venta_total"] == 3600
    assert coste_evento.datos["margen_bruto"] > 0
    assert coste_evento.datos["food_cost_porcentaje"] > 0

    sim = core.orquestador.resolver(SolicitudHostAI("simular_variacion_precio_receta", {
        "receta_id": "REC-CARRILLERA",
        "raciones": 80,
        "variacion_porcentaje": 15,
        "precio_venta_por_racion": 18,
    }))
    assert sim.ok is True
    assert sim.datos["impacto"]["diferencia_coste_total"] > 0

    diag = core.orquestador.resolver(SolicitudHostAI("diagnosticar_coste_evento", {
        "evento_id": evento_id,
        "food_cost_objetivo": 30,
    }))
    assert diag.ok is True
    assert "food_cost_actual" in diag.datos

    print("TEST OK - Host AI v2.0.6 Módulo Costes Inteligente")
    print("Coste receta:", coste_receta.to_dict())
    print("Coste evento:", coste_evento.to_dict())
    print("Simulación:", sim.to_dict())


if __name__ == "__main__":
    ejecutar_prueba()
