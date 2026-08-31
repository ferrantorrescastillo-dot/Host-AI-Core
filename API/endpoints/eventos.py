from __future__ import annotations

from API.contracts.http_models import ApiRequest, ApiResponse
from API.facade.core_public_facade import CorePublicFacade


def handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    return ApiResponse(status_code=200, payload=facade.eventos(request.query))

def detail_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    payload = facade.evento(str(request.path or "").rsplit("/", 1)[-1])
    return ApiResponse(status_code=200 if payload.get("ok") else int((payload.get("error") or {}).get("status") or 500), payload=payload)
