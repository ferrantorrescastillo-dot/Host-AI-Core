from __future__ import annotations

from API.contracts.http_models import ApiRequest, ApiResponse
from API.facade.core_public_facade import CorePublicFacade


def handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    path = str(request.path)
    if path.startswith("/api/v1/menus/"):
        menu_id = path.split("/api/v1/menus/", 1)[1].split("/", 1)[0]
        payload = facade.crear_plan_produccion_menu(menu_id, request.body)
    else:
        suffix = path.split("/api/v1/produccion/planes/", 1)[-1]
        plan_id = suffix.split("/", 1)[0]
        payload = (facade.crear_propuesta_compra_produccion(plan_id) if path.endswith("/propuesta-compra")
                   else facade.relacionar_articulo_produccion(plan_id, request.body) if path.endswith("/stock-resolution/article")
                   else facade.revision_stock_produccion(plan_id) if path.endswith("/stock-resolution")
                   else facade.plan_produccion(plan_id))
    status = (201 if request.method.upper() == "POST" and path.endswith("/plan-produccion") else 200) if payload.get("ok") else int((payload.get("error") or {}).get("status") or 500)
    return ApiResponse(status_code=status, payload=payload)
