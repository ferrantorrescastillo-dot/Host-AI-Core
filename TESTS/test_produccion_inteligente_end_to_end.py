from types import SimpleNamespace

from SERVICIOS.produccion_inteligente_workflow import IntelligentProductionWorkflow


class _Executor:
    def execute_agent_read(self, tool_id, _params):
        data = {
            "consultar_eventos": {"resultados": [{"id": "EVT-BODA", "nombre": "Boda sábado", "pax": 8, "menu_id": "MENU-1", "servicios": ["cena"], "fecha": "2026-08-29"}]},
            "consultar_evento_detalle": {"estado": "OK", "evento": {"evento_id": "EVT-BODA", "nombre": "Boda sábado", "pax": 8, "servicios": [{"servicio_id": "SERV-1", "pases": [{"pase_id": "PASE-1", "menu_id": "MENU-1"}]}]}},
            "consultar_produccion": {"resultados": [{"titulo": "Montaje", "estado": "bloqueada", "bloqueo": "Falta stock"}]},
            "consultar_menu": {"estado": "OK", "menu": {"menu_id": "MENU-1", "elaboraciones": [{"elaboracion_id": "REC-A"}, {"elaboracion_id": "REC-B"}]}},
            "consultar_escandallos": {"detalles": [
                {"id": "REC-A", "nombre": "Plato", "rendimiento": 4, "ingredientes": [{"articulo_id": "ART-PAT", "nombre_articulo": "Patata", "cantidad": 1000, "unidad": "g", "escandallo_hijo_id": "REC-B"}]},
                {"id": "REC-B", "nombre": "Fondo", "rendimiento": 0, "ingredientes": [{"articulo_id": "ART-AGUA", "nombre_articulo": "Agua", "cantidad": 1, "unidad": "l", "referencia_elaboracion": "REC-A"}]},
            ]},
            "consultar_estado_stock": {"articulos": [{"articulo_id": "ART-PAT", "cantidad": 1, "unidad": "kg"}]},
            "consultar_compras_pendientes": {"pedidos": [{"estado": "pedido", "lineas": [{"articulo_id": "ART-PAT", "pendiente": 500}]}]},
        }
        return SimpleNamespace(datos=data[tool_id])


def test_agregado_produccion_calcula_necesidad_faltante_dependencias_y_ciclo() -> None:
    result = IntelligentProductionWorkflow(_Executor()).investigate("boda")
    aggregate = result.aggregate

    assert aggregate["coverage"][0]["cantidad_necesaria"] == 2000
    assert aggregate["coverage"][0]["stock_utilizable"] == 1000
    assert aggregate["coverage"][0]["faltante_pre_compra"] == 1000
    assert aggregate["coverage"][0]["faltante_final"] == 500
    assert aggregate["dependencies"]["ciclos"]
    assert result.blocked[0]["bloqueo"] == "Falta stock"
    assert aggregate["unknown"]
    assert "Falta comprar" in result.summary


def test_kg_l_se_marca_como_conversion_faltante() -> None:
    coverage = IntelligentProductionWorkflow._coverage(
        [{"articulo_id": "ART-LIQ", "cantidad_necesaria": 2, "unidad": "l"}],
        {"articulos": [{"articulo_id": "ART-LIQ", "cantidad": 2, "unidad": "kg"}]}, {"pedidos": []},
    )

    assert coverage[0]["conversion_faltante"] is True
    assert coverage[0]["stock_utilizable"] == 0


def test_evento_resuelve_menu_desde_servicio_sin_menu_directo() -> None:
    event = {"servicios": [{"pases": [{"menu_id": "MENU-PASE"}]}]}

    assert IntelligentProductionWorkflow._menu_reference(event) == ("MENU-PASE", "")


def test_agregado_con_servicios_sin_menu_conserva_estado_parcial() -> None:
    class Executor:
        def execute_agent_read(self, tool_id, _params):
            if tool_id == "consultar_compras_pendientes":
                return SimpleNamespace(datos={"pedidos": []})
            return SimpleNamespace(datos={})

    result = IntelligentProductionWorkflow(Executor()).investigate(
        active_event={"id": "EVT-1", "nombre": "Evento", "pax": 10, "servicios": [{"nombre": "Cena"}]},
    )

    assert result.aggregate["recipes"] == []
    assert result.aggregate["needs"] == []
    assert result.unknown == ["plan de producción asociado"]