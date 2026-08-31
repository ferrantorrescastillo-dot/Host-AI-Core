from __future__ import annotations

from API.contracts.http_models import ApiRequest, ApiResponse
from API.facade.core_public_facade import CorePublicFacade
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext


def _internal_context(request: ApiRequest) -> AuthorizedExecutionContext:
    return AuthorizedExecutionContext.from_internal_environment(
        str(request.request_id or "").strip(), role="stock-web", allow_local_default=True,
    )


def movement_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    payload = facade.registrar_movimiento_stock(request.body)
    status = 201 if payload.get("ok") else int((payload.get("error") or {}).get("status") or 500)
    return ApiResponse(status_code=status, payload=payload)

def adjustment_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    operation = "confirm" if request.path.endswith("/confirmar") else "discard" if request.path.endswith("/descartar") else "preview"
    return _response(facade.ajuste_stock(request.body, _internal_context(request), operation=operation))

def locations_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    return _response(facade.ubicaciones_stock())

def lot_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    lot_id = str(request.path).split("/lotes/", 1)[-1].split("/", 1)[0]
    if request.path.endswith("/ubicacion/preview"):
        return _response(facade.ubicacion_lote(lot_id, request.body, _internal_context(request), confirm=False))
    if request.path.endswith("/ubicacion/confirmar"):
        return _response(facade.ubicacion_lote(lot_id, request.body, _internal_context(request), confirm=True))
    return _response(facade.lote_stock(lot_id))

def _response(payload: dict) -> ApiResponse:
    return ApiResponse(status_code=200 if payload.get("ok") else int((payload.get("error") or {}).get("status") or 500), payload=payload)
