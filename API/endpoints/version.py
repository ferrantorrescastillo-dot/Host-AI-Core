from __future__ import annotations

from API.contracts.http_models import ApiRequest, ApiResponse
from API.facade.core_public_facade import CorePublicFacade


def handle(_request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    return ApiResponse(status_code=200, payload=facade.version())
