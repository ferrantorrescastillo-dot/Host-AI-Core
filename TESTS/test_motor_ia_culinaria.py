from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI


def preparar_stock(core):
    entradas = [
        {"nombre": "Carrillera de ternera", "cantidad": 6, "unidad": "kg", "familia": "carnes", "articulo_id": "ART-CARRILLERA"},
        {"nombre": "Demi-glace", "cantidad": 2, "unidad": "L", "familia": "salsas", "articulo_id": "ART-DEMI"},
        {"nombre": "Patata", "cantidad": 10, "unidad": "kg", "familia": "verduras", "articulo_id": "ART-PATATA"},
        {"nombre": "Cebolla", "cantidad": 4, "unidad": "kg", "familia": "verduras", "articulo_id": "ART-CEBOLLA"},
    ]
    for e in entradas:
        r = core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", e))
        assert r.ok is True


def ejecutar_prueba():
    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "ia_culinaria" for p in listado.datos["pipelines"])

    preparar_stock(core)

    propuestas = core.orquestador.resolver(SolicitudHostAI("proponer_platos_stock", {
        "objetivo": "comida_personal",
        "raciones": 8,
        "estilo": "aprovechamiento gastronómico",
        "limitar": 3,
    }))
    assert propuestas.ok is True
    assert len(propuestas.datos["ideas"]) >= 1
    idea_id = propuestas.datos["ideas"][0]["id"]

    analisis = core.orquestador.resolver(SolicitudHostAI("analizar_idea_culinaria", {
        "idea_id": idea_id,
    }))
    assert analisis.ok is True
    assert "estado" in analisis.datos

    esc = core.orquestador.resolver(SolicitudHostAI("convertir_idea_escandallo", {
        "idea_id": idea_id,
        "receta_id": "REC-IA-APROVECHAMIENTO",
        "raciones_base": 8,
    }))
    assert esc.ok is True
    assert esc.datos["escandallo"]["receta_id"] == "REC-IA-APROVECHAMIENTO"
    assert len(esc.datos["escandallo"]["lineas"]) >= 1

    calc = core.orquestador.resolver(SolicitudHostAI("calcular_escandallo_receta", {
        "receta_id": "REC-IA-APROVECHAMIENTO",
        "raciones": 8,
    }))
    assert calc.ok is True
    assert len(calc.datos["necesidades"]) >= 1

    manual = core.orquestador.resolver(SolicitudHostAI("crear_idea_culinaria", {
        "nombre": "Arroz meloso de carrillera",
        "objetivo": "servicio",
        "raciones": 10,
        "tecnica_principal": "arroz meloso",
        "ingredientes": [
            {"nombre": "Carrillera de ternera", "cantidad": 1.8, "unidad": "kg", "articulo_id": "ART-CARRILLERA", "familia": "carnes"},
            {"nombre": "Demi-glace", "cantidad": 1.0, "unidad": "L", "articulo_id": "ART-DEMI", "familia": "salsas"},
            {"nombre": "Arroz", "cantidad": 1.0, "unidad": "kg", "disponible": False, "familia": "secos"},
        ],
    }))
    assert manual.ok is True
    manual_id = manual.datos["id"]

    analisis_manual = core.orquestador.resolver(SolicitudHostAI("analizar_idea_culinaria", {
        "idea_id": manual_id,
    }))
    assert analisis_manual.ok is True
    assert analisis_manual.requiere_aprobacion is True
    assert len(analisis_manual.datos["faltantes"]) >= 1

    print("TEST OK - Host AI v2.0.8 Motor de IA Culinaria")
    print("Propuestas:", propuestas.to_dict())
    print("Escandallo desde idea:", esc.to_dict())
    print("Análisis manual:", analisis_manual.to_dict())


if __name__ == "__main__":
    ejecutar_prueba()
