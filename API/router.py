from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from API.contracts.http_models import ApiRequest, ApiResponse
from API.endpoints import ai_costs, articulos, biblioteca, catalog_crud, chat, compras, dashboard, eventos, executive, health, menus, plan, produccion, reservas, stock, version, workflow
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
    Route("GET", "/api/v1/ai-costs/summary", ai_costs.summary_handle),
    Route("POST", "/api/v1/stock/movimientos", stock.movement_handle),
    Route("POST", "/api/v1/stock/ajustes/preview", stock.adjustment_handle),
    Route("POST", "/api/v1/stock/ajustes/confirmar", stock.adjustment_handle),
    Route("POST", "/api/v1/stock/ajustes/descartar", stock.adjustment_handle),
    Route("GET", "/api/v1/stock/ubicaciones", stock.locations_handle),
    Route("GET", "/api/v1/articulos", articulos.list_handle),
    Route("GET", "/api/v1/articulos/sin-precio", articulos.missing_prices_handle),
    Route("GET", "/api/v1/articulos/sin-precio/exportar", articulos.export_prices_handle),
    Route("GET", "/api/v1/articulos/reclasificacion/candidatos", articulos.reclassification_handle),
    Route("POST", "/api/v1/articulos/reclasificacion/preview", articulos.reclassification_handle),
    Route("POST", "/api/v1/articulos/reclasificacion/confirmar", articulos.reclassification_handle),
    Route("POST", "/api/v1/articulos/referencias-importadas/preview", articulos.import_prices_handle),
    Route("POST", "/api/v1/articulos/referencias-importadas/confirmar", articulos.import_prices_handle),
    Route("GET", "/api/v1/articulos/referencias-importadas/estado", articulos.import_prices_state_handle),
    Route("POST", "/api/v1/articulos/referencias-importadas/descartar", articulos.import_prices_discard_handle),
    Route("GET", "/api/v1/biblioteca", biblioteca.summary_handle),
    Route("GET", "/api/v1/biblioteca/elaboraciones", biblioteca.list_handle),
    Route("POST", "/api/v1/biblioteca/importaciones", biblioteca.import_create_handle),
    Route("GET", "/api/v1/biblioteca/importaciones", biblioteca.import_list_handle),
    Route("GET", "/api/v1/biblioteca/importaciones/activa", biblioteca.import_active_handle),
    Route("POST", "/api/v1/biblioteca/recetas/completado-externo/exportar", biblioteca.external_completion_handle),
    Route("POST", "/api/v1/biblioteca/recetas/completado-externo/importar", biblioteca.external_completion_handle),
    Route("GET", "/api/v1/menus", menus.collection_handle),
    Route("POST", "/api/v1/menus", menus.collection_handle),
    Route("GET", "/api/v1/menus/elaboraciones", menus.elaborations_handle),
    Route("GET", "/api/v1/reservas", reservas.collection_handle),
    Route("POST", "/api/v1/reservas/preview", reservas.preview_handle),
    Route("POST", "/api/v1/reservas/confirmar", reservas.confirm_handle),
    Route("GET", "/executive", executive.handle),
    Route("GET", "/dashboard", dashboard.handle),
    Route("GET", "/eventos", eventos.handle),
    Route("POST", "/api/v1/catalogo/preview", catalog_crud.preview_handle),
    Route("POST", "/api/v1/catalogo/confirmar", catalog_crud.confirm_handle),
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
        if handler is None and key[1].startswith("/api/v1/biblioteca/recetas/completado-ia/") and key[0] in {"GET", "POST"}:
            handler = biblioteca.batch_documentation_handle
        if handler is None and key[0] == "POST" and key[1].startswith("/api/v1/articulos/"):
            if key[1] == "/api/v1/articulos/documentacion/propuesta-borrador":
                handler = articulos.draft_documentation_handle
            elif "/documentacion/" in key[1]:
                handler = articulos.documentation_handle
            elif "/precio-referencia-web/" in key[1]:
                handler = articulos.web_price_handle
            elif "/precio-referencia-manual/" in key[1]:
                handler = articulos.manual_price_handle
            elif key[1].endswith("/formato/preview"):
                handler = articulos.format_preview_handle
            elif key[1].endswith("/formato/confirmar"):
                handler = articulos.format_confirm_handle
        if handler is None and key[0] in {"GET", "PATCH"} and key[1].startswith("/api/v1/articulos/"):
            handler = articulos.detail_handle if key[0] == "GET" else articulos.update_handle
        if handler is None and key[0] == "GET" and key[1].startswith("/api/v1/eventos/"):
            handler = eventos.detail_handle
        if handler is None and key[0] == "POST" and key[1].startswith("/api/v1/biblioteca/elaboraciones/"):
            if key[1].endswith("/rendimiento/preview"):
                handler = biblioteca.yield_preview_handle
            elif key[1].endswith("/rendimiento/confirmar"):
                handler = biblioteca.yield_confirm_handle
            elif "/escandallo/" in key[1]:
                handler = biblioteca.costing_handle
            elif "/documentacion/" in key[1]:
                handler = biblioteca.documentation_handle
        if handler is None and key[1].startswith("/api/v1/stock/lotes/") and key[0] in {"GET", "POST"}:
            handler = stock.lot_handle
        if handler is None and key[0] == "GET" and key[1].startswith("/api/v1/biblioteca/elaboraciones/"):
            handler = biblioteca.detail_handle
        if handler is None and key[0] in {"GET", "POST", "PATCH"} and key[1].startswith("/api/v1/biblioteca/importaciones/"):
            if key[0] == "POST" and "/canonicalizacion-existentes/" in key[1]:
                handler = biblioteca.import_legacy_canonicalization_handle
            elif key[0] == "POST" and key[1].endswith("/confirmar"):
                handler = biblioteca.import_confirm_handle
            elif key[0] == "GET" and key[1].endswith("/estado"):
                handler = biblioteca.import_status_handle
            elif key[0] == "GET" and key[1].endswith("/historial"):
                handler = biblioteca.import_history_handle
            elif key[0] == "GET" and key[1].endswith("/completado-recetas-activo"):
                handler = biblioteca.import_external_completion_active_handle
            elif key[0] == "POST" and key[1].endswith("/descartar"):
                handler = biblioteca.import_discard_handle
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
        if handler is None and key[0] == "GET" and key[1].startswith("/api/v1/reservas/"):
            handler = reservas.detail_handle
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
        if handler is None and key[0] in {"GET", "POST"} and key[1].startswith("/api/v1/produccion/planes/") and "/stock-resolution" in key[1]:
            handler = produccion.handle
        if handler is None and key == ("POST", "/api/v1/compras/borradores"):
            handler = compras.create_manual_draft_handle
        if handler is None and key[0] == "POST" and key[1].startswith("/api/v1/compras/borradores/") and key[1].endswith("/confirmar"):
            handler = compras.confirm_draft_handle
        if handler is None and key[0] in {"GET", "PATCH"} and key[1].startswith("/api/v1/compras/borradores/"):
            handler = compras.draft_handle
        if handler is None and key[0] == "POST" and key[1].startswith("/api/v1/compras/pedidos/") and key[1].endswith("/recepciones"):
            handler = compras.reception_handle
        if handler is None and key[0] in {"GET", "PATCH", "POST"} and key[1].startswith("/api/v1/compras/recepciones/"):
            handler = compras.reception_handle
        if key[0] in {"GET", "POST", "DELETE"} and key[1].startswith("/api/v1/compras/recepciones/") and key[1].endswith("/documento"):
            handler = compras.reception_document_handle
        if key[0] == "POST" and key[1].startswith("/api/v1/compras/recepciones/") and (key[1].endswith("/documento/analizar") or key[1].endswith("/extraccion/aplicar")):
            handler = compras.reception_extraction_handle
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
