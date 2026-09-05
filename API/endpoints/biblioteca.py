from __future__ import annotations

from API.contracts.http_models import ApiRequest, ApiResponse
from API.facade.core_public_facade import CorePublicFacade
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext


def summary_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    return _response(facade.biblioteca())


def list_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    return _response(facade.elaboraciones(request.query))


def detail_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    elaboration_id = str(request.path or "").rsplit("/", 1)[-1]
    payload = facade.elaboracion(elaboration_id)
    payload["permisos"] = {
        "confirmar_rendimiento": _can_confirm_yield(_internal_context(request)),
    }
    return _response(payload)


def yield_preview_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    elaboration_id = _elaboration_id(request.path)
    return _response(facade.previsualizar_rendimiento_elaboracion(
        elaboration_id, request.body, _internal_context(request),
    ))


def yield_confirm_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    elaboration_id = _elaboration_id(request.path)
    return _response(facade.confirmar_rendimiento_elaboracion(
        elaboration_id, request.body, _internal_context(request),
    ))

def costing_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    elaboration_id = _elaboration_id(request.path)
    return _response(facade.editar_escandallo(elaboration_id, request.body, _internal_context(request), confirm=request.path.endswith("/confirmar")))

def documentation_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    elaboration_id = _elaboration_id(request.path)
    operation = "confirm" if request.path.endswith("/confirmar") else "proposal" if request.path.endswith("/propuesta") else "preview"
    return _response(facade.documentacion_receta(elaboration_id, request.body, _internal_context(request), operation=operation))


def batch_documentation_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    parts = request.path.rstrip("/").split("/")
    operation = parts[-1]
    batch_id = "" if operation in {"resumen", "iniciar"} else parts[-2]
    operation = {"resumen": "summary", "iniciar": "start", "estado": "get", "siguiente": "next", "cancelar": "cancel", "reintentar": "retry", "reintentar-fallidas": "retry_failed", "seleccion": "select", "preview": "preview", "confirmar": "confirm"}[operation]
    return _response(facade.documentacion_recetas_masiva(batch_id, request.body, _internal_context(request), operation=operation))


def external_completion_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    operation = str(request.path or "").rstrip("/").rsplit("/", 1)[-1]
    if operation == "exportar":
        return _response(facade.exportar_completado_recetas(request.body))
    return _response(facade.importar_completado_recetas(request.body))


def import_create_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    return _response(facade.crear_importacion_biblioteca(request.body))


def import_list_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    return _response(facade.listar_importaciones_biblioteca())


def import_active_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    return _response(facade.importacion_biblioteca_activa())


def import_detail_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    import_id = str(request.path or "").split("/importaciones/", 1)[-1].split("/", 1)[0]
    return _response(facade.importacion_biblioteca(import_id))


def import_external_completion_active_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    import_id = str(request.path or "").split("/importaciones/", 1)[-1].split("/", 1)[0]
    return _response(facade.completado_externo_activo_importacion(import_id))


def import_discard_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    import_id = str(request.path or "").split("/importaciones/", 1)[-1].split("/", 1)[0]
    return _response(facade.descartar_importacion_biblioteca(import_id))


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


def import_confirm_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    import_id = str(request.path or "").split("/importaciones/", 1)[-1].split("/", 1)[0]
    return _response(facade.confirmar_importacion_biblioteca(import_id, request.body))


def import_legacy_canonicalization_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    import_id = str(request.path or "").split("/importaciones/", 1)[-1].split("/", 1)[0]
    if request.path.endswith("/preview"):
        return _response(facade.previsualizar_canonicalizacion_legacy_importacion(
            import_id, request.body, _internal_context(request),
        ))
    return _response(facade.confirmar_canonicalizacion_legacy_importacion(
        import_id, request.body, _internal_context(request),
    ))


def import_status_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    import_id = str(request.path or "").split("/importaciones/", 1)[-1].split("/", 1)[0]
    return _response(facade.estado_importacion_biblioteca(import_id))


def import_history_handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    import_id = str(request.path or "").split("/importaciones/", 1)[-1].split("/", 1)[0]
    return _response(facade.historial_importacion_biblioteca(import_id))


def _response(payload: dict) -> ApiResponse:
    status = 200 if payload.get("ok") else int((payload.get("error") or {}).get("status") or 500)
    return ApiResponse(status_code=status, payload=payload)


def _elaboration_id(path: str) -> str:
    tail = str(path or "").split("/elaboraciones/", 1)[-1]
    for marker in ("/rendimiento/", "/escandallo/", "/documentacion/"):
        tail = tail.split(marker, 1)[0]
    return tail


def _internal_context(request: ApiRequest) -> AuthorizedExecutionContext:
    return AuthorizedExecutionContext.from_internal_environment(
        str(request.request_id or "").strip(), role="biblioteca-web", allow_local_default=True,
    )


def _can_confirm_yield(context: AuthorizedExecutionContext) -> bool:
    valid, _reason = context.validate()
    return valid and "escandallos:write" in context.scopes
