from __future__ import annotations

from API.contracts.http_models import ApiRequest, ApiResponse
from API.facade.core_public_facade import CorePublicFacade


def draft_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    pedido_id = str(request.path).split("/api/v1/compras/borradores/", 1)[-1]
    payload = facade.actualizar_borrador_compra(pedido_id, request.body) if request.method.upper() == "PATCH" else facade.borrador_compra(pedido_id)
    status = 200 if payload.get("ok") else int((payload.get("error") or {}).get("status") or 500)
    return ApiResponse(status_code=status, payload=payload)
