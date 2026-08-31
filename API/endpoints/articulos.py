from __future__ import annotations

from API.contracts.http_models import ApiRequest, ApiResponse
from API.facade.core_public_facade import CorePublicFacade
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext


def list_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    payload = facade.articulos(request.query)
    return ApiResponse(status_code=_status(payload), payload=payload)


def detail_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    article_id = str(request.path or "").rsplit("/", 1)[-1]
    payload = facade.articulo(article_id)
    return ApiResponse(status_code=_status(payload), payload=payload)


def update_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    article_id = str(request.path or "").rsplit("/", 1)[-1]
    payload = facade.actualizar_articulo(article_id, request.body)
    return ApiResponse(status_code=_status(payload), payload=payload)


def format_preview_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    article_id = _format_article_id(request.path)
    payload = facade.previsualizar_formato_articulo(article_id, request.body, _internal_context(request))
    return ApiResponse(status_code=_status(payload), payload=payload)


def format_confirm_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    article_id = _format_article_id(request.path)
    payload = facade.confirmar_formato_articulo(article_id, request.body, _internal_context(request))
    return ApiResponse(status_code=_status(payload), payload=payload)


def documentation_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    article_id = _article_id(request.path)
    operation = "confirm" if request.path.endswith("/confirmar") else "preview" if request.path.endswith("/preview") else "proposal"
    payload = facade.documentacion_articulo(article_id, request.body, _internal_context(request), operation=operation)
    return ApiResponse(status_code=_status(payload), payload=payload)


def draft_documentation_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    payload = facade.propuesta_borrador_articulo(request.body)
    return ApiResponse(status_code=_status(payload), payload=payload)


def manual_price_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    article_id = _article_id(request.path)
    payload = facade.referencia_manual_articulo(article_id, request.body, _internal_context(request), confirm=request.path.endswith("/confirmar"))
    return ApiResponse(status_code=_status(payload), payload=payload)


def missing_prices_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    payload = facade.articulos_sin_precio()
    return ApiResponse(status_code=_status(payload), payload=payload)


def reclassification_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    operation = "candidates" if request.method == "GET" else "confirm" if request.path.endswith("/confirmar") else "preview"
    payload = facade.reclasificacion_articulos(request.body, _internal_context(request), operation=operation)
    return ApiResponse(status_code=_status(payload), payload=payload)


def export_prices_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    payload = facade.exportar_articulos_sin_precio()
    return ApiResponse(status_code=_status(payload), payload=payload)


def import_prices_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    payload = facade.importar_referencias_precio(request.body, _internal_context(request), confirm=request.path.endswith("/confirmar"))
    return ApiResponse(status_code=_status(payload), payload=payload)


def web_price_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    article_id = _article_id(request.path)
    payload = facade.referencia_web_articulo(article_id, request.body, _internal_context(request), confirm=request.path.endswith("/confirmar"))
    return ApiResponse(status_code=_status(payload), payload=payload)


def _article_id(path: str) -> str:
    return str(path or "").split("/articulos/", 1)[-1].split("/", 1)[0]


def _format_article_id(path: str) -> str:
    return str(path or "").split("/articulos/", 1)[-1].split("/formato/", 1)[0]


def _internal_context(request: ApiRequest) -> AuthorizedExecutionContext:
    return AuthorizedExecutionContext.from_internal_environment(
        str(request.request_id or "").strip(), role="articulos-web", allow_local_default=True,
    )


def _status(payload: dict) -> int:
    if payload.get("ok"):
        return 200
    return int((payload.get("error") or {}).get("status") or 500)
