from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from API.contracts.http_models import ApiRequest, ApiResponse
from API.endpoints import articulos, biblioteca, chat, compras, dashboard, eventos, executive, health, menus, plan, produccion, version, workflow
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
    Route("GET", "/api/v1/articulos", articulos.list_handle),
    Route("GET", "/api/v1/biblioteca", biblioteca.summary_handle),
    Route("GET", "/api/v1/biblioteca/elaboraciones", biblioteca.list_handle),
    Route("POST", "/api/v1/biblioteca/importaciones", biblioteca.import_create_handle),
    Route("GET", "/api/v1/menus", menus.collection_handle),
    Route("POST", "/api/v1/menus", menus.collection_handle),
    Route("GET", "/api/v1/menus/elaboraciones", menus.elaborations_handle),
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
        if handler is None and key[0] == "GET" and key[1].startswith("/api/v1/articulos/"):
            handler = articulos.detail_handle
        if handler is None and key[0] == "GET" and key[1].startswith("/api/v1/biblioteca/elaboraciones/"):
            handler = biblioteca.detail_handle
        if handler is None and key[0] in {"GET", "POST", "PATCH"} and key[1].startswith("/api/v1/biblioteca/importaciones/"):
            if key[0] == "POST" and key[1].endswith("/confirmar"):
                handler = biblioteca.import_confirm_handle
            elif key[0] == "GET" and key[1].endswith("/estado"):
                handler = biblioteca.import_status_handle
            elif key[0] == "GET" and key[1].endswith("/historial"):
                handler = biblioteca.import_history_handle
            elif key[1].endswith("/borrador"):
                handler = biblioteca.import_draft_handle
            elif key[0] == "GET" and key[1].endswith("/propuestas"):
                handler = biblioteca.import_proposals_handle
            elif key[0] == "GET":
                handler = biblioteca.import_detail_handle
        if handler is None and key[0] in {"GET", "PATCH", "DELETE"} and key[1].startswith("/api/v1/menus/"):
            if key[1].endswith("/necesidades"):
                handler = menus.needs_handle
            elif "/propuesta-compra/" in key[1] and key[0] in {"GET", "PATCH"}:
                handler = menus.proposal_handle
            else:
                handler = menus.detail_handle
        if handler is None and key[0] == "POST" and key[1].startswith("/api/v1/menus/") and key[1].endswith("/propuesta-compra"):
            handler = menus.proposal_handle
        if handler is None and key[0] == "POST" and "/propuesta-compra/" in key[1] and key[1].endswith("/crear-pedidos"):
            handler = menus.proposal_handle
        if handler is None and key[0] == "POST" and key[1].startswith("/api/v1/menus/") and key[1].endswith("/plan-produccion"):
            handler = produccion.handle
        if handler is None and key[0] == "GET" and key[1].startswith("/api/v1/produccion/planes/") and "/tareas/" not in key[1]:
            handler = produccion.handle
        if handler is None and key[0] == "POST" and key[1].startswith("/api/v1/produccion/planes/") and key[1].endswith("/propuesta-compra"):
            handler = produccion.handle
        if handler is None and key[0] == "POST" and key[1].startswith("/api/v1/compras/borradores/") and key[1].endswith("/confirmar"):
            handler = compras.confirm_draft_handle
        if handler is None and key[0] in {"GET", "PATCH"} and key[1].startswith("/api/v1/compras/borradores/"):
            handler = compras.draft_handle
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
