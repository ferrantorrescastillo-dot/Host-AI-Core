from __future__ import annotations

from API.contracts.http_models import ApiRequest, ApiResponse
from API.facade.core_public_facade import CorePublicFacade
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext


def collection_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    payload = facade.reservas(request.query)
    status = int(((payload.get("error") or {}).get("status") or 200))
    return ApiResponse(status_code=status, payload=payload)


def detail_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    reserva_id = str(request.path).removeprefix("/api/v1/reservas/").strip("/")
    payload = facade.reserva(reserva_id)
    status = int(((payload.get("error") or {}).get("status") or 200))
    return ApiResponse(status_code=status, payload=payload)


def preview_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    payload = facade.previsualizar_reserva(request.body, _internal_context(request))
    return ApiResponse(status_code=int(((payload.get("error") or {}).get("status") or 200)), payload=payload)


def confirm_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    payload = facade.confirmar_operacion_reserva(request.body, _internal_context(request))
    return ApiResponse(status_code=int(((payload.get("error") or {}).get("status") or 200)), payload=payload)


def _internal_context(request: ApiRequest) -> AuthorizedExecutionContext:
    return AuthorizedExecutionContext.from_internal_environment(
        request.request_id, role="web", allow_local_default=True,
    )
