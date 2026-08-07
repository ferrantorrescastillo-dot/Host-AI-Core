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
        parts = suffix.split("/")
        plan_id = parts[0]
        if path.endswith("/consumo-previsto"):
            payload = facade.consumo_previsto_produccion(plan_id, parts[2])
        elif path.endswith("/confirmar"):
            payload = facade.confirmar_produccion(plan_id, parts[2], request.body)
        else:
            payload = facade.plan_produccion(plan_id)
    status = (201 if request.method.upper() == "POST" and path.endswith("/plan-produccion") else 200) if payload.get("ok") else int((payload.get("error") or {}).get("status") or 500)
    return ApiResponse(status_code=status, payload=payload)
