from pathlib import Path
import sys
from datetime import date

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def crear_evento(core):
    ev = core.orquestador.resolver(SolicitudHostAI("crear_evento", {
        "nombre": "Evento escandallo real",
        "fecha": date.today().isoformat(),
        "pax": 80,
        "tipo": "catering",
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
    assert any(p["nombre"] == "escandallos" for p in listado.datos["pipelines"])

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
    assert esc.datos["escandallo"]["coste_total_base"] > 0

    calc = core.orquestador.resolver(SolicitudHostAI("calcular_escandallo_receta", {
        "receta_id": "REC-CARRILLERA",
        "raciones": 80,
    }))
    assert calc.ok is True
    assert calc.datos["raciones_calculadas"] == 80
    assert len(calc.datos["necesidades"]) == 2
    carrillera = [n for n in calc.datos["necesidades"] if n["nombre"] == "Carrillera de ternera"][0]
    assert round(carrillera["cantidad_bruta"], 2) == 15.84

    evento_id = crear_evento(core)

    # Metemos stock parcial para comprobar que producción completa usa escandallo real.
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {
        "nombre": "Carrillera de ternera",
        "cantidad": 5,
        "unidad": "kg",
        "articulo_id": "ART-CARRILLERA",
    }))

    calc_evento = core.orquestador.resolver(SolicitudHostAI("calcular_escandallo_evento", {
        "evento_id": evento_id,
    }))
    assert calc_evento.ok is True
    assert calc_evento.datos["coste_total_estimado"] > 0
    assert len(calc_evento.datos["necesidades_agregadas"]) == 2

    informe = core.orquestador.resolver(SolicitudHostAI("analizar_produccion_completa_evento", {
        "evento_id": evento_id,
        "generar_compras": True,
    }))
    assert informe.ok is True
    assert informe.requiere_aprobacion is True
    assert any(n["nombre"] == "Carrillera de ternera" for n in informe.datos["necesidades"])
    assert len(informe.datos["compras_generadas"]) >= 1

    print("TEST OK - Host AI v1.0.5 Motor de Escandallos Inteligente")
    print("Cálculo receta:", calc.to_dict())
    print("Informe producción:", informe.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
