from __future__ import annotations

from API.contracts.http_models import ApiRequest, ApiResponse
from API.facade.core_public_facade import CorePublicFacade


def handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    return ApiResponse(status_code=200, payload=facade.eventos(request.query))
