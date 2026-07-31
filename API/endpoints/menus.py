from __future__ import annotations

from API.contracts.http_models import ApiRequest, ApiResponse
from API.facade.core_public_facade import CorePublicFacade


def collection_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    payload = (
        facade.crear_menu(request.body)
        if request.method.upper() == "POST"
        else facade.menus(request.query)
    )
    return _response(payload, created=request.method.upper() == "POST")


def elaborations_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    return _response(facade.elaboraciones_menu(request.query))


def detail_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    menu_id = str(request.path or "").split("/api/v1/menus/", 1)[-1]
    if request.method.upper() == "PATCH":
        payload = facade.actualizar_menu(menu_id, request.body)
    elif request.method.upper() == "DELETE":
        payload = facade.archivar_menu(menu_id, request.body)
    else:
        payload = facade.menu(menu_id)
    return _response(payload)


def needs_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    menu_id = str(request.path).split("/api/v1/menus/", 1)[-1].split("/", 1)[0]
    return _response(facade.necesidades_menu(menu_id))


def proposal_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    suffix = str(request.path).split("/api/v1/menus/", 1)[-1]
    parts = suffix.split("/")
    menu_id = parts[0]
    payload = (
        facade.crear_propuesta_compra_menu(menu_id)
        if request.method.upper() == "POST"
        else facade.propuesta_compra_menu(menu_id, parts[-1])
    )
    return _response(payload, created=request.method.upper() == "POST")


def _response(payload: dict, created: bool = False) -> ApiResponse:
    if payload.get("ok"):
        status = 201 if created else 200
    else:
        status = int((payload.get("error") or {}).get("status") or 500)
    return ApiResponse(status_code=status, payload=payload)
