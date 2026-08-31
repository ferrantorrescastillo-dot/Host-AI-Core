import json

from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


def _agent():
    return HostAIAgent(None, None, HostAIToolCatalog.for_general_agent(build_default_tool_registry()))


def test_proyeccion_recetas_conserva_datos_criticos_y_reduce_tamano():
    raw = {
        "estado": "OK", "detalles": [{
            "id": "REC-1", "nombre": "Salsa", "rendimiento": 4, "unidad_rendimiento": "u",
            "estado_coste": "PARCIAL", "ingredientes": [{
                "nombre_articulo": "Patata", "articulo_id": "ART-PAT", "cantidad": 1000, "unidad": "g",
                "estado_relacion": "RELACIONADO", "documentacion_extensa": "x" * 10000,
            }], "historico": ["x" * 10000], "documentos": ["x" * 10000],
        }], "no_encontrados": [], "total_encontrados": 1,
    }

    projected = _agent()._project_result(raw)

    assert len(json.dumps(projected)) < len(json.dumps(raw)) / 5
    recipe = projected["recetas"][0]
    assert recipe["id"] == "REC-1"
    assert recipe["rendimiento"] == 4
    assert recipe["ingredientes"][0]["cantidad"] == 1000
    assert "historico" not in projected["recetas"][0]


def test_proyeccion_evento_conserva_pases_y_recetas():
    raw = {"estado": "OK", "evento": {
        "evento_id": "EVT-1", "nombre": "Boda", "fecha": "2099-01-01", "pax": 50,
        "servicios": [{"servicio_id": "SERV-1", "nombre": "Cena", "pases": [{"pase_id": "P-1", "recetas": ["REC-1"]}]}],
        "metadatos": "x" * 10000,
    }}

    projected = _agent()._project_result(raw)

    assert projected["evento"]["evento_id"] == "EVT-1"
    assert projected["evento"]["servicios"][0]["pases"][0]["recetas"] == ["REC-1"]
    assert "metadatos" not in projected["evento"]