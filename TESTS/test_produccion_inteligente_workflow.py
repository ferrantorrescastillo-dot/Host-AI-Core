from types import SimpleNamespace
from datetime import date, timedelta

from SERVICIOS.produccion_inteligente_workflow import IntelligentProductionWorkflow
from SERVICIOS.produccion_inteligente_workflow import ProductionInvestigation


class _Executor:
    def execute_agent_read(self, tool_id, _params):
        if tool_id == "consultar_eventos":
            return SimpleNamespace(datos={"resultados": [{"id": "EVT-1", "nombre": "Boda Boronat", "pax": 80, "servicios": ["cena"]}]})
        return SimpleNamespace(datos={"resultados": [{"titulo": "Carrillera", "cantidad": 80, "unidad": "raciones", "estado": "bloqueada", "bloqueo": "Falta stock", "evento_id": "EVT-1"}]})


def test_produccion_resuelve_evento_y_no_inventa_datos() -> None:
    result = IntelligentProductionWorkflow(_Executor()).investigate("boda")

    assert result.event["id"] == "EVT-1"
    assert result.blocked[0]["bloqueo"] == "Falta stock"
    assert "Carrillera" in result.summary
    assert result.unknown == []


def test_proximo_evento_selecciona_fecha_mas_cercana_y_admite_formatos_mixtos() -> None:
    today = date.today()
    selected, diagnosis = IntelligentProductionWorkflow._select_next_event([
        {"id": "FUTURO", "fecha": (today + timedelta(days=30)).strftime("%d/%m/%Y"), "estado": "confirmado"},
        {"id": "HOY", "fecha": today.isoformat(), "estado": "confirmado"},
        {"id": "PASADO", "fecha": (today - timedelta(days=1)).strftime("%d/%m/%Y"), "estado": "confirmado"},
        {"id": "CANCELADO", "fecha": (today + timedelta(days=1)).isoformat(), "estado": "cancelado"},
        {"id": "INVALIDO", "fecha": "fecha rota", "estado": "confirmado"},
    ])

    assert selected["id"] == "HOY"
    assert diagnosis == "fechas inválidas ignoradas"


def test_proximo_evento_empata_solo_con_misma_fecha_y_hora() -> None:
    future = (date.today() + timedelta(days=1)).isoformat()
    selected, diagnosis = IntelligentProductionWorkflow._select_next_event([
        {"id": "A", "fecha": future, "hora_inicio": "12:00", "estado": "confirmado"},
        {"id": "B", "fecha": future, "hora_inicio": "12:00", "estado": "confirmado"},
    ])

    assert selected is None
    assert diagnosis == "hay varios eventos con la misma fecha y hora"


def test_sintesis_profesional_incluye_produccion_bloqueos_compras_y_pendientes() -> None:
    result = ProductionInvestigation(
        "resumen corto", {"nombre": "Boda"}, [{"titulo": "Montaje", "bloqueo": "Falta horno"}],
        [{"titulo": "Montaje", "bloqueo": "Falta horno"}], ["tiempos de Salsa"], {
            "needs": [{"nombre": "Patata", "cantidad_necesaria": 8, "unidad": "kg"}],
            "coverage": [{"nombre": "Patata", "faltante_final": 3, "unidad": "kg"}],
            "dependencies": {"orden_tecnico": ["REC-BASE", "REC-PLATO"], "ciclos": []},
            "ai_proposals": [{"tipo": "AI_PROPOSAL"}],
        },
    )

    text = IntelligentProductionWorkflow.professional_summary(result)

    assert "Producción calculada" in text
    assert "Bloqueos" in text
    assert "Compras y cobertura" in text
    assert "Antes de cerrar el plan" in text