from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from API.app import HostAIPlatformAPI
from API.contracts.http_models import ApiRequest, ApiResponse
from API.infra.response_envelope import build_error_payload
from SERVICIOS.hostai_import_ai_export_service import (
    HostAIImportAIExportError,
    HostAIImportAIExportService,
)


def _base_dir_from_env() -> Path:
    raw = str(os.getenv("HOST_AI_BASE_DIR", "")).strip()
    if raw:
        return Path(raw).resolve()
    return Path(__file__).resolve().parent.parent


def _parse_query(request: Request) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in request.query_params.multi_items():
        if key in out:
            prev = out[key]
            if isinstance(prev, list):
                prev.append(value)
            else:
                out[key] = [prev, value]
        else:
            out[key] = value
    return out


def _parse_allowed_origins() -> list[str]:
    raw = str(os.getenv("HOST_AI_API_CORS_ALLOWED_ORIGINS", "http://localhost:5173")).strip()
    values = [item.strip() for item in raw.split(",") if item.strip()]
    env_name = str(os.getenv("HOST_AI_API_ENV", "development")).strip().lower()
    allow_wildcard = str(os.getenv("HOST_AI_API_ALLOW_WILDCARD_CORS", "false")).strip().lower() in {
        "1",
        "true",
        "yes",
    }

    safe_values: list[str] = []
    for origin in values:
        if origin == "*":
            if env_name == "development" and allow_wildcard:
                safe_values.append(origin)
            continue
        safe_values.append(origin)

    if env_name == "development":
        safe_values.extend(
            [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:5174",
                "http://127.0.0.1:5174",
                "http://localhost:5176",
                "http://127.0.0.1:5176",
                "http://localhost:5178",
                "http://127.0.0.1:5178",
            ]
        )

    safe_values = list(dict.fromkeys(safe_values))
    if not safe_values:
        safe_values = ["http://localhost:5173"]
    return safe_values


def _build_json_response(result: ApiResponse) -> JSONResponse:
    return JSONResponse(status_code=int(result.status_code), content=dict(result.payload or {}))


def create_app(platform_api: HostAIPlatformAPI | None = None) -> FastAPI:
    api = platform_api or HostAIPlatformAPI(base_dir=_base_dir_from_env())

    app = FastAPI(title="Host AI Platform API", version="1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_parse_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "Content-Disposition", "X-HostAI-Domain-Writes"],
    )

    async def _delegate(request: Request, body: dict[str, Any] | None = None) -> JSONResponse:
        request_id = str(request.headers.get("x-request-id") or "").strip()
        payload_body = dict(body or {})
        if not request_id:
            request_id = str(payload_body.get("request_id") or "").strip()
        if not request_id:
            request_id = str(uuid4())

        api_request = ApiRequest(
            method=str(request.method or "GET").upper(),
            path=str(request.url.path or ""),
            request_id=request_id,
            query=_parse_query(request),
            headers={k.lower(): v for k, v in request.headers.items()},
            body=payload_body,
        )

        try:
            result = api.handle(api_request)
            return _build_json_response(result)
        except Exception:
            payload = build_error_payload(
                request_id=request_id,
                status_code=500,
                code="internal_error",
                message="No se pudo procesar la solicitud.",
            )
            return JSONResponse(status_code=500, content=payload)

    async def _json_body(request: Request) -> dict[str, Any]:
        try:
            payload = await request.json()
        except Exception:
            return {}
        return dict(payload) if isinstance(payload, dict) else {}

    @app.get("/api/v1/health")
    async def get_health(request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.get("/api/v1/version")
    async def get_version(request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.get("/api/v1/executive")
    async def get_executive(request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.get("/api/v1/dashboard")
    async def get_dashboard(request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.get("/api/v1/ai-costs/summary")
    async def get_ai_cost_summary(request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.post("/api/v1/stock/movimientos")
    async def post_stock_movimiento(request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/stock/ajustes/preview")
    async def post_stock_ajuste_preview(request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/stock/ajustes/confirmar")
    async def post_stock_ajuste_confirm(request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/stock/ajustes/descartar")
    async def post_stock_ajuste_discard(request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.get("/api/v1/stock/ubicaciones")
    async def get_stock_ubicaciones(request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.get("/api/v1/stock/lotes/{lote_id}")
    async def get_stock_lote(lote_id: str, request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.post("/api/v1/stock/lotes/{lote_id}/ubicacion/preview")
    async def post_stock_lote_ubicacion_preview(lote_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/stock/lotes/{lote_id}/ubicacion/confirmar")
    async def post_stock_lote_ubicacion_confirm(lote_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.get("/api/v1/articulos")
    async def get_articulos(request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.get("/api/v1/articulos/sin-precio")
    async def get_articulos_sin_precio(request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.get("/api/v1/articulos/sin-precio/exportar")
    async def get_articulos_sin_precio_exportar(request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.get("/api/v1/articulos/reclasificacion/candidatos")
    async def get_articulos_reclasificacion_candidatos(request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.post("/api/v1/articulos/reclasificacion/preview")
    async def post_articulos_reclasificacion_preview(request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/articulos/reclasificacion/confirmar")
    async def post_articulos_reclasificacion_confirmar(request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/articulos/referencias-importadas/preview")
    async def post_referencias_importadas_preview(request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/articulos/referencias-importadas/confirmar")
    async def post_referencias_importadas_confirmar(request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.get("/api/v1/eventos/{evento_id}")
    async def get_evento(evento_id: str, request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.post("/api/v1/catalogo/preview")
    async def post_catalogo_preview(request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/catalogo/confirmar")
    async def post_catalogo_confirmar(request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/reservas/preview")
    async def post_reservas_preview(request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/reservas/confirmar")
    async def post_reservas_confirmar(request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.get("/api/v1/articulos/{articulo_id}")
    async def get_articulo(articulo_id: str, request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.patch("/api/v1/articulos/{articulo_id}")
    async def patch_articulo(articulo_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/articulos/{articulo_id}/documentacion/propuesta")
    async def post_articulo_documentacion_propuesta(articulo_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/articulos/documentacion/propuesta-borrador")
    async def post_articulo_borrador_propuesta(request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/articulos/{articulo_id}/documentacion/preview")
    async def post_articulo_documentacion_preview(articulo_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/articulos/{articulo_id}/documentacion/confirmar")
    async def post_articulo_documentacion_confirmar(articulo_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/articulos/{articulo_id}/precio-referencia-manual/preview")
    async def post_articulo_precio_manual_preview(articulo_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/articulos/{articulo_id}/precio-referencia-manual/confirmar")
    async def post_articulo_precio_manual_confirmar(articulo_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/articulos/{articulo_id}/precio-referencia-web/preview")
    async def post_articulo_precio_web_preview(articulo_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/articulos/{articulo_id}/precio-referencia-web/confirmar")
    async def post_articulo_precio_web_confirmar(articulo_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.get("/api/v1/biblioteca")
    async def get_biblioteca(request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.get("/api/v1/biblioteca/elaboraciones")
    async def get_elaboraciones(request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.get("/api/v1/biblioteca/elaboraciones/{elaboracion_id}")
    async def get_elaboracion(elaboracion_id: str, request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.get("/api/v1/menus")
    async def get_menus(request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.post("/api/v1/menus")
    async def post_menu(request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.get("/api/v1/menus/elaboraciones")
    async def get_menu_elaboraciones(request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.get("/api/v1/menus/{menu_id}")
    async def get_menu(menu_id: str, request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.patch("/api/v1/menus/{menu_id}")
    async def patch_menu(menu_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.delete("/api/v1/menus/{menu_id}")
    async def delete_menu(menu_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.get("/api/v1/menus/{menu_id}/necesidades")
    async def get_menu_necesidades(menu_id: str, request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.post("/api/v1/menus/{menu_id}/propuesta-compra")
    async def post_menu_propuesta_compra(menu_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.get("/api/v1/menus/{menu_id}/propuesta-compra/{proposal_id}")
    async def get_menu_propuesta_compra(menu_id: str, proposal_id: str, request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.patch("/api/v1/menus/{menu_id}/propuesta-compra/{proposal_id}")
    async def patch_menu_propuesta_compra(menu_id: str, proposal_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/menus/{menu_id}/propuesta-compra/{proposal_id}/crear-pedidos")
    async def post_menu_propuesta_pedidos(menu_id: str, proposal_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/menus/{menu_id}/plan-produccion")
    async def post_menu_plan_produccion(menu_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.get("/api/v1/produccion/planes/{plan_id}")
    async def get_plan_produccion(plan_id: str, request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.post("/api/v1/produccion/planes/{plan_id}/propuesta-compra")
    async def post_propuesta_compra_produccion(plan_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.get("/api/v1/produccion/planes/{plan_id}/stock-resolution")
    async def get_revision_stock_produccion(plan_id: str, request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.post("/api/v1/produccion/planes/{plan_id}/stock-resolution/article")
    async def post_relacion_articulo_produccion(plan_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/produccion/planes/{plan_id}/stock-resolution/movement")
    async def post_stock_produccion(plan_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/compras/borradores")
    async def post_compras_borrador_manual(request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.get("/api/v1/compras/borradores/{pedido_id}")
    async def get_compras_borrador(pedido_id: str, request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.patch("/api/v1/compras/borradores/{pedido_id}")
    async def patch_compras_borrador(pedido_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/compras/borradores/{pedido_id}/confirmar")
    async def post_confirmar_compras_borrador(pedido_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/compras/pedidos/{pedido_id}/recepciones")
    async def post_compras_recepcion(pedido_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.get("/api/v1/compras/recepciones/{reception_id}")
    async def get_compras_recepcion(reception_id: str, request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.patch("/api/v1/compras/recepciones/{reception_id}")
    async def patch_compras_recepcion(reception_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/compras/recepciones/{reception_id}/confirmar")
    async def post_confirmar_compras_recepcion(reception_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/compras/recepciones/{reception_id}/documento")
    async def post_documento_compras_recepcion(reception_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.get("/api/v1/compras/recepciones/{reception_id}/documento")
    async def get_documento_compras_recepcion(reception_id: str, request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.delete("/api/v1/compras/recepciones/{reception_id}/documento")
    async def delete_documento_compras_recepcion(reception_id: str, request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.post("/api/v1/compras/recepciones/{reception_id}/documento/analizar")
    async def post_analizar_documento_compras_recepcion(reception_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/compras/recepciones/{reception_id}/extraccion/aplicar")
    async def post_aplicar_extraccion_compras_recepcion(reception_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/biblioteca/importaciones")
    async def post_biblioteca_importacion(request: Request) -> JSONResponse:
        parsed: dict[str, Any] = {}
        try:
            maybe_json = await request.json()
            if isinstance(maybe_json, dict):
                parsed = maybe_json
        except Exception:
            parsed = {}
        return await _delegate(request, body=parsed)

    @app.post("/api/v1/biblioteca/importaciones/preparar-para-ia")
    async def post_biblioteca_preparar_para_ia(request: Request) -> Response:
        parsed = await _json_body(request)
        try:
            service = HostAIImportAIExportService(api.facade.base_dir)
            filename, content = service.prepare(
                filename=str(parsed.get("nombre") or ""),
                content_base64=str(parsed.get("contenido_base64") or ""),
            )
        except HostAIImportAIExportError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "error": {"message": str(exc)}})
        return Response(
            content=content,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-HostAI-Domain-Writes": "0",
            },
        )

    @app.post("/api/v1/biblioteca/elaboraciones/{elaboracion_id}/rendimiento/preview")
    async def post_biblioteca_rendimiento_preview(
        elaboracion_id: str, request: Request,
    ) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/articulos/{articulo_id}/formato/preview")
    async def post_articulo_formato_preview(
        articulo_id: str, request: Request,
    ) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/articulos/{articulo_id}/formato/confirmar")
    async def post_articulo_formato_confirmar(
        articulo_id: str, request: Request,
    ) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/biblioteca/elaboraciones/{elaboracion_id}/rendimiento/confirmar")
    async def post_biblioteca_rendimiento_confirmar(
        elaboracion_id: str, request: Request,
    ) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/biblioteca/elaboraciones/{elaboracion_id}/escandallo/preview")
    async def post_biblioteca_escandallo_preview(elaboracion_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/biblioteca/elaboraciones/{elaboracion_id}/escandallo/confirmar")
    async def post_biblioteca_escandallo_confirm(elaboracion_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/biblioteca/elaboraciones/{elaboracion_id}/documentacion/propuesta")
    async def post_biblioteca_documentacion_proposal(elaboracion_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/biblioteca/elaboraciones/{elaboracion_id}/documentacion/preview")
    async def post_biblioteca_documentacion_preview(elaboracion_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/biblioteca/elaboraciones/{elaboracion_id}/documentacion/confirmar")
    async def post_biblioteca_documentacion_confirm(elaboracion_id: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.get("/api/v1/biblioteca/recetas/completado-ia/resumen")
    async def get_recipe_batch_summary(request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.post("/api/v1/biblioteca/recetas/completado-ia/iniciar")
    async def post_recipe_batch_start(request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.get("/api/v1/biblioteca/recetas/completado-ia/{batch_id}/estado")
    async def get_recipe_batch(batch_id: str, request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.post("/api/v1/biblioteca/recetas/completado-ia/{batch_id}/{operation}")
    async def post_recipe_batch(batch_id: str, operation: str, request: Request) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.get("/api/v1/biblioteca/importaciones/{importacion_id}")
    async def get_biblioteca_importacion(importacion_id: str, request: Request) -> JSONResponse:
        return await _delegate(request)

    @app.get("/api/v1/biblioteca/importaciones/{importacion_id}/propuestas")
    async def get_biblioteca_importacion_propuestas(
        importacion_id: str, request: Request
    ) -> JSONResponse:
        return await _delegate(request)

    @app.get("/api/v1/biblioteca/importaciones/{importacion_id}/borrador")
    async def get_biblioteca_importacion_borrador(
        importacion_id: str, request: Request
    ) -> JSONResponse:
        return await _delegate(request)

    @app.patch("/api/v1/biblioteca/importaciones/{importacion_id}/borrador")
    async def patch_biblioteca_importacion_borrador(
        importacion_id: str, request: Request
    ) -> JSONResponse:
        parsed: dict[str, Any] = {}
        try:
            maybe_json = await request.json()
            if isinstance(maybe_json, dict):
                parsed = maybe_json
        except Exception:
            parsed = {}
        return await _delegate(request, body=parsed)

    @app.post("/api/v1/biblioteca/importaciones/{importacion_id}/confirmar")
    async def post_biblioteca_importacion_confirmar(
        importacion_id: str, request: Request
    ) -> JSONResponse:
        parsed: dict[str, Any] = {}
        try:
            maybe_json = await request.json()
            if isinstance(maybe_json, dict):
                parsed = maybe_json
        except Exception:
            parsed = {}
        return await _delegate(request, body=parsed)

    @app.post("/api/v1/biblioteca/importaciones/{importacion_id}/canonicalizacion-existentes/preview")
    async def post_biblioteca_importacion_canonicalizacion_preview(
        importacion_id: str, request: Request
    ) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.post("/api/v1/biblioteca/importaciones/{importacion_id}/canonicalizacion-existentes/confirmar")
    async def post_biblioteca_importacion_canonicalizacion_confirmar(
        importacion_id: str, request: Request
    ) -> JSONResponse:
        return await _delegate(request, body=await _json_body(request))

    @app.get("/api/v1/biblioteca/importaciones/{importacion_id}/estado")
    async def get_biblioteca_importacion_estado(
        importacion_id: str, request: Request
    ) -> JSONResponse:
        return await _delegate(request)

    @app.get("/api/v1/biblioteca/importaciones/{importacion_id}/historial")
    async def get_biblioteca_importacion_historial(
        importacion_id: str, request: Request
    ) -> JSONResponse:
        return await _delegate(request)

    @app.post("/api/v1/chat")
    async def post_chat(request: Request) -> JSONResponse:
        parsed: dict[str, Any] = {}
        try:
            maybe_json = await request.json()
            if isinstance(maybe_json, dict):
                parsed = maybe_json
        except Exception:
            parsed = {}
        return await _delegate(request, body=parsed)

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def fallback(full_path: str, request: Request) -> JSONResponse:
        return await _delegate(request)

    return app


app = create_app()
