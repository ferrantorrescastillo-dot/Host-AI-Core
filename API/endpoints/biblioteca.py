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


def import_create_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    return _response(facade.crear_importacion_biblioteca(request.body))


def import_detail_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    import_id = str(request.path or "").split("/importaciones/", 1)[-1].split("/", 1)[0]
    return _response(facade.importacion_biblioteca(import_id))


def import_proposals_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    import_id = str(request.path or "").split("/importaciones/", 1)[-1].split("/", 1)[0]
    return _response(facade.propuestas_importacion_biblioteca(import_id))


def import_draft_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    import_id = str(request.path or "").split("/importaciones/", 1)[-1].split("/", 1)[0]
    if str(request.method or "").upper() == "PATCH":
        return _response(facade.actualizar_borrador_importacion_biblioteca(
            import_id, request.body
        ))
    return _response(facade.borrador_importacion_biblioteca(import_id))


def _response(payload: dict) -> ApiResponse:
    status = 200 if payload.get("ok") else int((payload.get("error") or {}).get("status") or 500)
    return ApiResponse(status_code=status, payload=payload)
