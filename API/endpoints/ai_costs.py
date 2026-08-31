from API.contracts.http_models import ApiRequest, ApiResponse
from API.facade.core_public_facade import CorePublicFacade


def summary_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    payload = facade.ai_cost_summary(request.query)
    return ApiResponse(status_code=200, payload=payload)
