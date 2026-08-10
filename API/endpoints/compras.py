from __future__ import annotations

from API.contracts.http_models import ApiRequest, ApiResponse
from API.facade.core_public_facade import CorePublicFacade


def create_manual_draft_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    payload = facade.crear_borrador_compra_manual(request.body)
    status = 201 if payload.get("ok") else int((payload.get("error") or {}).get("status") or 500)
    return ApiResponse(status_code=status, payload=payload)


def draft_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    pedido_id = str(request.path).split("/api/v1/compras/borradores/", 1)[-1]
    payload = facade.actualizar_borrador_compra(pedido_id, request.body) if request.method.upper() == "PATCH" else facade.borrador_compra(pedido_id)
    status = 200 if payload.get("ok") else int((payload.get("error") or {}).get("status") or 500)
    return ApiResponse(status_code=status, payload=payload)


def confirm_draft_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    pedido_id = str(request.path).split("/api/v1/compras/borradores/", 1)[-1].rsplit("/confirmar", 1)[0]
    payload = facade.confirmar_borrador_compra(pedido_id, request.body)
    status = 200 if payload.get("ok") else int((payload.get("error") or {}).get("status") or 500)
    return ApiResponse(status_code=status, payload=payload)


def reception_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    path = str(request.path)
    if "/pedidos/" in path:
        pedido_id = path.split("/api/v1/compras/pedidos/", 1)[-1].rsplit("/recepciones", 1)[0]
        payload = facade.crear_recepcion_compra(pedido_id, request.body)
        success_status = 201
    else:
        reception_id = path.split("/api/v1/compras/recepciones/", 1)[-1].rsplit("/confirmar", 1)[0]
        if request.method.upper() == "PATCH":
            payload = facade.actualizar_recepcion_compra(reception_id, request.body)
        elif path.endswith("/confirmar"):
            payload = facade.confirmar_recepcion_compra(reception_id, request.body)
        else:
            payload = facade.recepcion_compra(reception_id)
        success_status = 200
    status = success_status if payload.get("ok") else int((payload.get("error") or {}).get("status") or 500)
    return ApiResponse(status_code=status, payload=payload)


def reception_document_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    reception_id = str(request.path).split("/api/v1/compras/recepciones/", 1)[-1].rsplit("/documento", 1)[0]
    if request.method.upper() == "POST":
        payload = facade.adjuntar_documento_recepcion_compra(reception_id, request.body)
        success_status = 201
    elif request.method.upper() == "DELETE":
        payload = facade.quitar_documento_recepcion_compra(reception_id)
        success_status = 200
    else:
        payload = facade.documento_recepcion_compra(reception_id)
        success_status = 200
    status = success_status if payload.get("ok") else int((payload.get("error") or {}).get("status") or 500)
    return ApiResponse(status_code=status, payload=payload)
