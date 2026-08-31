from __future__ import annotations
from API.contracts.http_models import ApiRequest, ApiResponse
from API.facade.core_public_facade import CorePublicFacade
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext

def preview_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    return _response(facade.previsualizar_catalogo(request.body, _context(request)))

def confirm_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    return _response(facade.confirmar_catalogo(request.body, _context(request)))

def _context(request: ApiRequest) -> AuthorizedExecutionContext:
    return AuthorizedExecutionContext.from_internal_environment(
        str(request.request_id or "").strip(), role="catalog-web", allow_local_default=True,
    )

def _response(payload: dict) -> ApiResponse:
    return ApiResponse(status_code=200 if payload.get("ok") else int((payload.get("error") or {}).get("status") or 500), payload=payload)
