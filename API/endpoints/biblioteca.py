from __future__ import annotations

from API.contracts.http_models import ApiRequest, ApiResponse
from API.facade.core_public_facade import CorePublicFacade


def summary_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    return _response(facade.biblioteca())


def list_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    return _response(facade.elaboraciones(request.query))


def detail_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    elaboration_id = str(request.path or "").rsplit("/", 1)[-1]
    return _response(facade.elaboracion(elaboration_id))


def _response(payload: dict) -> ApiResponse:
    status = 200 if payload.get("ok") else int((payload.get("error") or {}).get("status") or 500)
    return ApiResponse(status_code=status, payload=payload)
