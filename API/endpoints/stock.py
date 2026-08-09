from __future__ import annotations

from API.contracts.http_models import ApiRequest, ApiResponse
from API.facade.core_public_facade import CorePublicFacade


def movement_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    payload = facade.registrar_movimiento_stock(request.body)
    status = 201 if payload.get("ok") else int((payload.get("error") or {}).get("status") or 500)
    return ApiResponse(status_code=status, payload=payload)
