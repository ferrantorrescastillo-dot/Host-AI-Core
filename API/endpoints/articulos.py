from __future__ import annotations

from API.contracts.http_models import ApiRequest, ApiResponse
from API.facade.core_public_facade import CorePublicFacade


def list_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    payload = facade.articulos(request.query)
    return ApiResponse(status_code=_status(payload), payload=payload)


def detail_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    article_id = str(request.path or "").rsplit("/", 1)[-1]
    payload = facade.articulo(article_id)
    return ApiResponse(status_code=_status(payload), payload=payload)


def _status(payload: dict) -> int:
    if payload.get("ok"):
        return 200
    return int((payload.get("error") or {}).get("status") or 500)
