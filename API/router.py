from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from API.contracts.http_models import ApiRequest, ApiResponse
from API.endpoints import chat, dashboard, eventos, executive, health, plan, version, workflow
from API.facade.core_public_facade import CorePublicFacade
from API.infra.response_envelope import build_error_payload, normalize_success_payload


Handler = Callable[[ApiRequest, CorePublicFacade], ApiResponse]


@dataclass(frozen=True)
class Route:
    method: str
    path: str
    handler: Handler


ROUTES: tuple[Route, ...] = (
    Route("GET", "/health", health.handle),
    Route("GET", "/version", version.handle),
    Route("GET", "/api/v1/health", health.handle),
    Route("GET", "/api/v1/version", version.handle),
    Route("GET", "/api/v1/executive", executive.handle),
    Route("GET", "/api/v1/dashboard", dashboard.handle),
    Route("GET", "/executive", executive.handle),
    Route("GET", "/dashboard", dashboard.handle),
    Route("GET", "/eventos", eventos.handle),
    Route("GET", "/workflow", workflow.handle),
    Route("GET", "/plan", plan.handle),
    Route("POST", "/api/v1/chat", chat.handle),
    Route("POST", "/chat", chat.handle),
)


class ApiRouter:
    def __init__(self, facade: CorePublicFacade):
        self.facade = facade
        self._table = {(r.method.upper(), r.path): r.handler for r in ROUTES}

    def dispatch(self, request: ApiRequest) -> ApiResponse:
        request_id = str(request.request_id or "")
        key = (str(request.method or "").upper(), str(request.path or ""))
        handler = self._table.get(key)
        if handler is None:
            return ApiResponse(
                status_code=404,
                payload=build_error_payload(
                    request_id=request_id,
                    status_code=404,
                    code="not_found",
                    message="Endpoint no encontrado.",
                ),
            )
        try:
            raw = handler(request, self.facade)
            return ApiResponse(
                status_code=int(raw.status_code),
                payload=normalize_success_payload(
                    request_id=request_id,
                    status_code=int(raw.status_code),
                    payload=dict(raw.payload or {}),
                ),
            )
        except Exception:
            return ApiResponse(
                status_code=500,
                payload=build_error_payload(
                    request_id=request_id,
                    status_code=500,
                    code="internal_error",
                    message="No se pudo procesar la solicitud.",
                ),
            )
