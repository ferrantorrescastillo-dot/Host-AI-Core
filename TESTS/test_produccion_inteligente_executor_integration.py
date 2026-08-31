import json

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI
from SERVICIOS.host_ai_home_read_service import HostAIHomeReadService
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry
from SERVICIOS.produccion_inteligente_workflow import IntelligentProductionWorkflow


def _resolve(core, intent, params):
    response = core.orquestador.resolver(SolicitudHostAI(intent, params))
    assert response.ok, response.mensaje
    return response.datos


def test_executor_real_resuelve_evento_servicio_pase_y_recetas_temporales(tmp_path):
    db = tmp_path / "DATOS" / "db"
    db.mkdir(parents=True)
    (db / "escandallos_canonicos.json").write_text(json.dumps({"escandallos": [{
        "receta": {"codigo": "REC-BASE", "nombre": "Base", "rendimiento": 4, "unidad_rendimiento": "u", "ingredientes": [{"codigo": "ART-PAT", "nombre": "Patata", "cantidad": 1000, "unidad": "g", "articulo_id": "ART-PAT"}]}, "coste_total": 0,
    }, {
        "receta": {"codigo": "REC-PLATO", "nombre": "Plato", "rendimiento": 4, "unidad_rendimiento": "u", "ingredientes": [{"codigo": "REC-BASE", "nombre": "Base", "cantidad": 1, "unidad": "u", "articulo_id": "REC-BASE", "metadata": {"tipo": "ELABORACION", "referencia_elaboracion": "REC-BASE"}}]}, "coste_total": 0,
    }, {
        "receta": {"codigo": "REC-LIQ", "nombre": "Salsa líquida", "rendimiento": 4, "unidad_rendimiento": "u", "ingredientes": [{"codigo": "ART-LIQ", "nombre": "Caldo", "cantidad": 1000, "unidad": "ml", "articulo_id": "ART-LIQ"}]}, "coste_total": 0,
    }, {
        "receta": {"codigo": "REC-INCOMP", "nombre": "Ingrediente incompatible", "rendimiento": 4, "unidad_rendimiento": "u", "ingredientes": [{"codigo": "ART-INCOMP", "nombre": "Concentrado", "cantidad": 1, "unidad": "l", "articulo_id": "ART-INCOMP"}]}, "coste_total": 0,
    }]}), encoding="utf-8")
    (db / "articulos.json").write_text(json.dumps([{"codigo": "ART-PAT", "nombre": "Patata", "unidad_base": "kg", "precio": 2}, {"codigo": "ART-LIQ", "nombre": "Caldo", "unidad_base": "l", "precio": 1}, {"codigo": "ART-INCOMP", "nombre": "Concentrado", "unidad_base": "kg", "precio": 1}]), encoding="utf-8")
    (db / "proveedores.json").write_text("[]", encoding="utf-8")
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")

    core = HostAICore(tmp_path)
    core.stock.registrar_entrada("Patata", 1, "kg", articulo_id="ART-PAT", ubicacion="seco", coste_unitario=2)
    core.stock.registrar_entrada("Caldo", 1, "l", articulo_id="ART-LIQ", ubicacion="frio", coste_unitario=1)
    core.stock.registrar_entrada("Concentrado", 1, "kg", articulo_id="ART-INCOMP", ubicacion="seco", coste_unitario=1)
    need = core.compras.registrar_necesidad("Patata", 2, "kg", articulo_id="ART-PAT", proveedor_preferente="Proveedor")
    active_order = core.compras.generar_pedidos_sugeridos()["pedidos_sugeridos"][0]
    core.compras.cambiar_estado_pedido(active_order["id"], "preparado")
    draft_need = core.compras.registrar_necesidad("Patata", 9, "kg", articulo_id="ART-PAT", proveedor_preferente="Proveedor")
    core.compras.generar_pedidos_sugeridos()
    liquid_need = core.compras.registrar_necesidad("Caldo", 1, "l", articulo_id="ART-LIQ", proveedor_preferente="Proveedor")
    liquid_order = core.compras.generar_pedidos_sugeridos()["pedidos_sugeridos"][0]
    core.compras.cambiar_estado_pedido(liquid_order["id"], "preparado")
    event = _resolve(core, "crear_evento", {"nombre": "Boda temporal", "fecha": "2026-09-01", "pax": 8, "tipo": "boda"})["evento"]
    service = _resolve(core, "agregar_servicio_evento", {"evento_id": event["id"], "nombre": "Cena", "hora_inicio": "20:00"})["evento"]["servicios"][0]
    course = _resolve(core, "agregar_pase_evento", {"evento_id": event["id"], "servicio_id": service["id"], "nombre": "Principal", "hora_inicio": "20:30", "recetas": ["REC-BASE", "REC-PLATO", "REC-LIQ", "REC-INCOMP"]})["evento"]["servicios"][0]["pases"][0]
    plan = _resolve(core, "planificar_produccion_real_evento", {"evento_id": event["id"], "hora_inicio": "10:00"})
    plan_id = plan.get("id") or plan.get("plan_id")
    task_id = core.produccion_real.resumen_ejecucion(plan_id)["tareas"][0]["id"]
    core.produccion_real.registrar_incidencia_tarea(plan_id, task_id, "bloqueo", "Falta equipo de cocción", gravedad="alta")

    executor = HostAIToolExecutor(build_default_tool_registry(), home_read_service=HostAIHomeReadService(core))
    detail = executor.execute_agent_read("consultar_evento_detalle", {"evento_id": event["id"]})
    stock_detail = executor.execute_agent_read("consultar_estado_stock", {"consulta": "articulo", "terminos": ["ART-PAT"]})
    before = (db / "escandallos_canonicos.json").read_bytes()
    result = IntelligentProductionWorkflow(executor).investigate(active_event={"id": event["id"], "nombre": event["nombre"]})

    assert detail.datos["evento"]["servicios"][0]["pases"][0]["pase_id"] == course["id"]
    assert detail.datos["evento"]["servicios"][0]["pases"][0]["recetas"] == ["REC-BASE", "REC-PLATO", "REC-LIQ", "REC-INCOMP"]
    assert {item["recipe_id"] for item in result.aggregate["needs"]} == {"REC-BASE", "REC-PLATO", "REC-LIQ", "REC-INCOMP"}
    assert result.aggregate["coverage"][0]["stock_utilizable"] == 1000, stock_detail.datos
    assert result.aggregate["coverage"][0]["compra_pendiente_utilizable"] == 2000
    assert result.aggregate["coverage"][0]["faltante_pre_compra"] == 1000
    assert result.aggregate["coverage"][0]["faltante_final"] == 0
    liquid = next(item for item in result.aggregate["coverage"] if item["articulo_id"] == "ART-LIQ")
    incompatible = next(item for item in result.aggregate["coverage"] if item["articulo_id"] == "ART-INCOMP")
    assert liquid["stock_utilizable"] == 1000 and liquid["compra_pendiente_utilizable"] == 1000
    assert liquid["faltante_pre_compra"] == 1000 and liquid["faltante_final"] == 0
    assert incompatible["conversion_faltante"] is True and incompatible["stock_utilizable"] == 0
    assert any(task["bloqueo"] == "Falta equipo de cocción" for task in result.blocked)
    assert (db / "escandallos_canonicos.json").read_bytes() == before
    assert result.to_dict()["datos_reales_modificados"] is False