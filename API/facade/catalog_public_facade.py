from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from API.facade.core_public_api02 import CorePublicApi02Facade
from SERVICIOS.articulos_catalog_read_service import ArticulosCatalogReadService
from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService
from SERVICIOS.importador_inteligente_biblioteca import ImportDocumentService
from SERVICIOS.menus_inteligentes_service import MenusInteligentesService
from SERVICIOS.menu_necesidades_service import MenuNecesidadesService
from SERVICIOS.compras_borradores_service import ComprasBorradoresService
from SERVICIOS.compras_recepciones_service import ComprasRecepcionesService
from SERVICIOS.compras_recepcion_extraction_service import ComprasRecepcionExtractionService
from SERVICIOS.menu_produccion_service import MenuProduccionService
from SERVICIOS.stock_ajustes_service import StockAjusteError, StockAjustesService
from SERVICIOS.confirmacion_rendimiento_elaboracion_service import (
    ConfirmacionRendimientoElaboracionService,
    ErrorConfirmacionRendimiento,
)
from SERVICIOS.confirmacion_formato_articulo_service import (
    ConfirmacionFormatoArticuloService,
    ErrorConfirmacionFormatoArticulo,
)
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.catalog_crud_write_service import CatalogCrudError, CatalogCrudWriteService
from SERVICIOS.stock_lote_write_service import StockLoteWriteError, StockLoteWriteService
from SERVICIOS.escandallo_editor_service import EscandalloEditorError, EscandalloEditorService
from SERVICIOS.receta_documentacion_write_service import HostAIRecipeProposalGenerator, RecetaDocumentacionError, RecetaDocumentacionWriteService
from SERVICIOS.receta_documentacion_batch_service import RecetaDocumentacionBatchService
from SERVICIOS.recipe_completion_exchange_service import RecipeCompletionExchangeService
from SERVICIOS.articulo_documentacion_write_service import ArticuloDocumentacionError, ArticuloDocumentacionWriteService, HostAIArticleProposalGenerator
from SERVICIOS.precio_referencia_web_service import PrecioReferenciaWebError, PrecioReferenciaWebService
from SERVICIOS.precio_referencias_import_service import PrecioReferenciasImportService
from SERVICIOS.reclasificacion_entidad_catalogo_service import ReclasificacionEntidadCatalogoService, ReclasificacionEntidadError


logger = logging.getLogger(__name__)


class CatalogPublicFacade(CorePublicApi02Facade):
    """Amplía la fachada certificada con consultas de catálogo de solo lectura."""

    def __init__(self, base_dir: Path | None = None) -> None:
        super().__init__(base_dir=base_dir)
        self._articulos_service: ArticulosCatalogReadService | None = None
        self._biblioteca_service: BibliotecaCulinariaReadService | None = None
        self._biblioteca_import_service: ImportDocumentService | None = None
        self._menus_service: MenusInteligentesService | None = None
        self._menu_needs_service: MenuNecesidadesService | None = None
        self._compras_drafts_service: ComprasBorradoresService | None = None
        self._compras_receptions_service: ComprasRecepcionesService | None = None
        self._compras_reception_extraction_service: ComprasRecepcionExtractionService | None = None
        self._menu_production_service: MenuProduccionService | None = None
        self._stock_adjustments_service: StockAjustesService | None = None
        self._yield_confirmation_service: ConfirmacionRendimientoElaboracionService | None = None
        self._article_format_confirmation_service: ConfirmacionFormatoArticuloService | None = None
        self._catalog_crud_service: CatalogCrudWriteService | None = None
        self._stock_lot_service: StockLoteWriteService | None = None
        self._costing_editor_service: EscandalloEditorService | None = None
        self._recipe_docs_service: RecetaDocumentacionWriteService | None = None
        self._recipe_docs_batch_service: RecetaDocumentacionBatchService | None = None
        self._recipe_completion_exchange_service: RecipeCompletionExchangeService | None = None
        self._article_docs_service: ArticuloDocumentacionWriteService | None = None
        self._manual_price_service: PrecioReferenciaWebService | None = None
        self._price_import_service: PrecioReferenciasImportService | None = None
        self._entity_reclassification_service: ReclasificacionEntidadCatalogoService | None = None

    def _get_price_reference_service(self) -> PrecioReferenciaWebService:
        if self._manual_price_service is None:
            self._manual_price_service = PrecioReferenciaWebService(self.base_dir)
        return self._manual_price_service

    def _get_catalog_crud_service(self) -> CatalogCrudWriteService:
        if self._catalog_crud_service is None: self._catalog_crud_service = CatalogCrudWriteService(self.base_dir)
        return self._catalog_crud_service

    def evento(self, evento_id: str) -> dict[str, Any]:
        item = self._get_catalog_crud_service().event_detail(evento_id)
        if item is None: return {**self._error_payload(code="event_not_found", message="Evento no encontrado."), "error": {"status": 404, "code": "event_not_found", "message": "Evento no encontrado."}}
        return {"ok": True, **self._base_payload(), "evento": item}

    def previsualizar_catalogo(self, body: dict[str, Any], context: AuthorizedExecutionContext) -> dict[str, Any]:
        payload = dict(body or {})
        try:
            return {**self._base_payload(), **self._get_catalog_crud_service().preview(domain=str(payload.get("dominio") or ""), operation=str(payload.get("operacion") or ""), entity_id=str(payload.get("entity_id") or ""), payload=dict(payload.get("payload") or {}), session_id=str(payload.get("session_id") or ""), context=context, field_origins=dict(payload.get("field_origins") or {}))}
        except CatalogCrudError as exc:
            status = 403 if exc.code == "unauthorized" else 404 if exc.code == "not_found" else 409 if exc.code in {"duplicate", "invalid_preview", "expired_preview", "stale_preview"} else 422
            return {**self._error_payload(code=exc.code, message=str(exc)), "error": {"status": status, "code": exc.code, "message": str(exc)}}

    def confirmar_catalogo(self, body: dict[str, Any], context: AuthorizedExecutionContext) -> dict[str, Any]:
        payload = dict(body or {})
        try:
            return {**self._base_payload(), **self._get_catalog_crud_service().confirm(preview_token=str(payload.get("preview_token") or ""), session_id=str(payload.get("session_id") or ""), context=context)}
        except CatalogCrudError as exc:
            status = 403 if exc.code == "unauthorized" else 409
            return {**self._error_payload(code=exc.code, message=str(exc)), "error": {"status": status, "code": exc.code, "message": str(exc)}}

    def _get_articulos_service(self) -> ArticulosCatalogReadService:
        if self._articulos_service is None:
            self._articulos_service = ArticulosCatalogReadService(
                self.base_dir,
                stock=self._get_core().stock,
                compras=self._get_core().compras,
            )
        return self._articulos_service

    def articulos(self, query: dict[str, Any]) -> dict[str, Any]:
        try:
            result = self._get_articulos_service().listar(dict(query or {}))
            return {**self._base_payload(), **result}
        except Exception:
            return self._error_payload(
                code="catalog_unavailable",
                message="No se pudo consultar el catálogo.",
            )

    def articulo(self, articulo_id: str) -> dict[str, Any]:
        try:
            result = self._get_articulos_service().obtener(articulo_id)
            return {**self._base_payload(), **result}
        except Exception:
            return self._error_payload(
                code="catalog_unavailable",
                message="No se pudo consultar el artículo.",
            )

    def _get_article_docs_service(self) -> ArticuloDocumentacionWriteService:
        if self._article_docs_service is None:
            self._article_docs_service = ArticuloDocumentacionWriteService(self.base_dir, generator=HostAIArticleProposalGenerator(self.base_dir, engine=self._get_core().orquestador.host_ai_engine))
        return self._article_docs_service

    def documentacion_articulo(self, article_id: str, body: dict[str, Any], context: AuthorizedExecutionContext, *, operation: str) -> dict[str, Any]:
        service = self._get_article_docs_service(); payload = dict(body or {})
        if operation == "proposal": return self._safe_operational_call(service.proposal, article_id=article_id, proposed=dict(payload.get("proposed") or {}), session_id=str(payload.get("session_id") or ""), culinary_context=dict(payload.get("culinary_context") or {}))
        method = service.confirm if operation == "confirm" else service.preview
        kwargs = {"article_id": article_id, "selected": dict(payload.get("selected") or {}), "context": context}
        if operation == "confirm": kwargs["preview_token"] = str(payload.get("preview_token") or "")
        return self._safe_operational_call(method, **kwargs)

    def propuesta_borrador_articulo(self, body: dict[str, Any]) -> dict[str, Any]:
        payload = dict(body or {})
        return self._safe_operational_call(self._get_article_docs_service().draft_proposal, draft=dict(payload.get("draft") or {}), proposed=dict(payload.get("proposed") or {}), session_id=str(payload.get("session_id") or ""), culinary_context=dict(payload.get("culinary_context") or {}))

    def referencia_manual_articulo(self, article_id: str, body: dict[str, Any], context: AuthorizedExecutionContext, *, confirm: bool) -> dict[str, Any]:
        service = self._get_price_reference_service()
        payload = dict(body or {}); method = service.confirm_manual if confirm else service.preview_manual
        kwargs = {"article_id": article_id, "result": dict(payload.get("result") or payload), "context": context}
        if confirm: kwargs["preview_token"] = str(payload.get("preview_token") or "")
        return self._safe_operational_call(method, **kwargs)

    def _get_price_import_service(self) -> PrecioReferenciasImportService:
        if self._price_import_service is None: self._price_import_service = PrecioReferenciasImportService(self.base_dir, self._get_price_reference_service())
        return self._price_import_service

    def articulos_sin_precio(self) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_price_import_service().missing_articles()}

    def reclasificacion_articulos(self, body: dict[str, Any], context: AuthorizedExecutionContext, *, operation: str) -> dict[str, Any]:
        if self._entity_reclassification_service is None:
            self._entity_reclassification_service = ReclasificacionEntidadCatalogoService(self.base_dir)
        service = self._entity_reclassification_service; payload = dict(body or {})
        try:
            if operation == "candidates": result = service.candidates()
            elif operation == "confirm": result = service.confirm(list(payload.get("rows") or []), str(payload.get("preview_token") or ""), context)
            else: result = service.preview(list(payload.get("rows") or []), context)
            return {**self._base_payload(), **result}
        except ReclasificacionEntidadError as exc:
            status = 403 if exc.code == "unauthorized" else 404 if exc.code == "article_not_found" else 409 if exc.code == "stale_or_invalid_preview" else 422
            return {**self._error_payload(code=exc.code, message=str(exc)), "error": {"status": status, "code": exc.code, "message": str(exc)}}

    def exportar_articulos_sin_precio(self) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_price_import_service().export_text()}

    def importar_referencias_precio(self, body: dict[str, Any], context: AuthorizedExecutionContext, *, confirm: bool) -> dict[str, Any]:
        payload = dict(body or {})
        method = self._get_price_import_service().confirm if confirm else self._get_price_import_service().preview
        kwargs = {"context": context, "rows": list(payload.get("rows") or [])} if confirm else {"context": context, "raw": str(payload.get("raw") or "")}
        return {**self._base_payload(), **method(**kwargs)}

    def estado_referencias_precio(self, context: AuthorizedExecutionContext) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_price_import_service().active(context)}

    def descartar_referencias_precio(self, context: AuthorizedExecutionContext) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_price_import_service().discard(context)}

    def ai_cost_summary(self, query: dict[str, Any]) -> dict[str, Any]:
        payload = dict(query or {})
        summary = self._get_core().orquestador.host_ai_engine.ai_costs.aggregate(session_id=str(payload.get("session_id") or ""), entity_type=str(payload.get("entity_type") or ""), entity_id=str(payload.get("entity_id") or ""), period=str(payload.get("period") or ""))
        return {**self._base_payload(), "cost_summary": summary, "datos_reales_modificados": False}

    def referencia_web_articulo(self, article_id: str, body: dict[str, Any], context: AuthorizedExecutionContext, *, confirm: bool) -> dict[str, Any]:
        service = self._get_price_reference_service(); payload = dict(body or {})
        method = service.confirm if confirm else service.preview
        kwargs = {"article_id": article_id, "result": dict(payload.get("result") or {}), "context": context}
        if confirm: kwargs["preview_token"] = str(payload.get("preview_token") or "")
        return self._safe_operational_call(method, **kwargs)

    def actualizar_articulo(self, articulo_id: str, body: dict[str, Any]) -> dict[str, Any]:
        try:
            result = self._get_articulos_service().actualizar(articulo_id, dict(body or {}))
            return {**self._base_payload(), **result}
        except Exception:
            return self._error_payload(code="article_update_failed", message="No se pudo actualizar el artículo.")

    def _get_article_format_confirmation_service(self) -> ConfirmacionFormatoArticuloService:
        if self._article_format_confirmation_service is None:
            self._article_format_confirmation_service = ConfirmacionFormatoArticuloService(
                self.base_dir, self._get_articulos_service(),
            )
        return self._article_format_confirmation_service

    def previsualizar_formato_articulo(
        self, articulo_id: str, body: dict[str, Any], context: AuthorizedExecutionContext,
    ) -> dict[str, Any]:
        return self._article_format_call("preview", articulo_id, body, context)

    def confirmar_formato_articulo(
        self, articulo_id: str, body: dict[str, Any], context: AuthorizedExecutionContext,
    ) -> dict[str, Any]:
        return self._article_format_call("execute", articulo_id, body, context)

    def _article_format_call(
        self, operation_name: str, articulo_id: str, body: dict[str, Any],
        context: AuthorizedExecutionContext,
    ) -> dict[str, Any]:
        payload = dict(body or {})
        operation = getattr(self._get_article_format_confirmation_service(), operation_name)
        try:
            result = operation(
                article_id=articulo_id,
                precio=payload.get("precio"),
                unidad_compra=str(payload.get("unidad_compra") or ""),
                cantidad_formato=payload.get("cantidad_formato"),
                unidad_formato=str(payload.get("unidad_formato") or ""),
                cantidad_uso=payload.get("cantidad_uso"),
                unidad_uso=str(payload.get("unidad_uso") or ""),
                context=context,
                **({"preview_token": str(payload.get("preview_token") or "")} if operation_name == "execute" else {}),
            )
            return {**self._base_payload(), **result}
        except ErrorConfirmacionFormatoArticulo as exc:
            status = 403 if exc.code == "unauthorized" else 404 if exc.code == "article_not_found" else 409 if exc.code == "stale_or_invalid_preview" else 422
            error = self._error_payload(code=exc.code, message=str(exc))
            error["error"]["status"] = status
            return error
        except Exception:
            logger.exception("Error al confirmar el formato de un articulo.")
            return self._error_payload(
                code="article_format_confirmation_failed",
                message="No se pudo confirmar el formato del artículo.",
            )

    def _get_stock_adjustments_service(self) -> StockAjustesService:
        if self._stock_adjustments_service is None:
            self._stock_adjustments_service = StockAjustesService(self._get_core())
        return self._stock_adjustments_service

    def registrar_movimiento_stock(self, body: dict[str, Any]) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_stock_adjustments_service().registrar(dict(body or {}))}

    def ajuste_stock(self, body: dict[str, Any], context: AuthorizedExecutionContext, *, operation: str) -> dict[str, Any]:
        service = self._get_stock_adjustments_service()
        method = service.confirm if operation == "confirm" else service.discard if operation == "discard" else service.preview
        return self._safe_operational_call(method, dict(body or {}), context)

    def _get_stock_lot_service(self) -> StockLoteWriteService:
        if self._stock_lot_service is None: self._stock_lot_service = StockLoteWriteService(self._get_core())
        return self._stock_lot_service

    def lote_stock(self, lot_id: str) -> dict[str, Any]:
        return self._safe_operational_call(self._get_stock_lot_service().detail, lot_id)

    def ubicaciones_stock(self) -> dict[str, Any]:
        return self._safe_operational_call(self._get_stock_lot_service().locations)

    def ubicacion_lote(self, lot_id: str, body: dict[str, Any], context: AuthorizedExecutionContext, *, confirm: bool) -> dict[str, Any]:
        service = self._get_stock_lot_service(); payload = dict(body or {})
        method = service.confirm_location if confirm else service.preview_location
        kwargs = {"lot_id": lot_id, "location_id": str(payload.get("location_id") or ""), "context": context}
        if confirm: kwargs["preview_token"] = str(payload.get("preview_token") or "")
        return self._safe_operational_call(method, **kwargs)

    def _get_biblioteca_service(self) -> BibliotecaCulinariaReadService:
        if self._biblioteca_service is None:
            self._biblioteca_service = BibliotecaCulinariaReadService(self.base_dir)
        return self._biblioteca_service

    def _get_costing_editor_service(self) -> EscandalloEditorService:
        if self._costing_editor_service is None: self._costing_editor_service = EscandalloEditorService(self.base_dir)
        return self._costing_editor_service

    def editar_escandallo(self, elaboration_id: str, body: dict[str, Any], context: AuthorizedExecutionContext, *, confirm: bool) -> dict[str, Any]:
        payload = dict(body or {}); service = self._get_costing_editor_service()
        method = service.confirm if confirm else service.preview
        kwargs = {"escandallo_id": elaboration_id, "changes": dict(payload.get("changes") or {}), "context": context}
        if confirm: kwargs["preview_token"] = str(payload.get("preview_token") or "")
        return self._safe_operational_call(method, **kwargs)

    def _get_recipe_docs_service(self) -> RecetaDocumentacionWriteService:
        if self._recipe_docs_service is None:
            engine = self._get_core().orquestador.host_ai_engine
            self._recipe_docs_service = RecetaDocumentacionWriteService(
                self.base_dir,
                generator=HostAIRecipeProposalGenerator(self.base_dir, engine=engine),
            )
        return self._recipe_docs_service

    def documentacion_receta(self, elaboration_id: str, body: dict[str, Any], context: AuthorizedExecutionContext, *, operation: str) -> dict[str, Any]:
        service = self._get_recipe_docs_service(); payload = dict(body or {})
        if operation == "proposal": return self._safe_operational_call(service.proposal, recipe_id=elaboration_id, proposed=dict(payload.get("proposed") or {}), detected_allergens=list(payload.get("detected_allergens") or []), session_id=str(payload.get("session_id") or ""))
        method = service.confirm if operation == "confirm" else service.preview
        kwargs = {"recipe_id": elaboration_id, "selected": dict(payload.get("selected") or {}), "overwrite_fields": list(payload.get("overwrite_fields") or []), "context": context}
        if operation == "confirm": kwargs["preview_token"] = str(payload.get("preview_token") or "")
        return self._safe_operational_call(method, **kwargs)

    def documentacion_recetas_masiva(self, batch_id: str, body: dict[str, Any], context: AuthorizedExecutionContext, *, operation: str) -> dict[str, Any]:
        service = self._get_recipe_docs_batch_service()
        payload = dict(body or {})
        methods = {
            "summary": lambda: service.summary(),
            "start": lambda: service.start(
                recipe_ids=(list(payload.get("recipe_ids") or []) if "recipe_ids" in payload else None)
            ),
            "get": lambda: service.get(batch_id),
            "next": lambda: service.next(batch_id, session_id=str(payload.get("session_id") or "")),
            "cancel": lambda: service.cancel(batch_id),
            "retry": lambda: service.retry(batch_id, str(payload.get("recipe_id") or "")),
            "retry_failed": lambda: service.retry_failed(batch_id),
            "select": lambda: service.select(
                batch_id,
                dict(payload.get("selections") or {}),
                (dict(payload.get("individual_selections") or {}) if "individual_selections" in payload else None),
                (dict(payload.get("grouped_selections") or {}) if "grouped_selections" in payload else None),
            ),
            "preview": lambda: service.preview(batch_id, context=context),
            "confirm": lambda: service.confirm(batch_id, fingerprint=str(payload.get("fingerprint") or ""), context=context),
        }
        return self._safe_operational_call(methods[operation])

    def _get_recipe_docs_batch_service(self) -> RecetaDocumentacionBatchService:
        if self._recipe_docs_batch_service is None:
            self._recipe_docs_batch_service = RecetaDocumentacionBatchService(
                self.base_dir, recipe_service=self._get_recipe_docs_service(),
            )
        return self._recipe_docs_batch_service

    def _get_recipe_completion_exchange_service(self) -> RecipeCompletionExchangeService:
        if self._recipe_completion_exchange_service is None:
            recipe_service = self._get_recipe_docs_service()
            batch_service = self._get_recipe_docs_batch_service()
            self._recipe_completion_exchange_service = RecipeCompletionExchangeService(
                self.base_dir, recipe_service=recipe_service,
                repository=recipe_service.repository, batch_service=batch_service,
            )
        return self._recipe_completion_exchange_service

    def exportar_completado_recetas(self, body: dict[str, Any]) -> dict[str, Any]:
        payload = dict(body or {})
        return self._safe_operational_call(
            self._get_recipe_completion_exchange_service().export,
            recipe_ids=list(payload.get("recipe_ids") or []),
            scope=str(payload.get("scope") or "BIBLIOTECA"),
            import_id=str(payload.get("import_id") or ""),
        )

    def importar_completado_recetas(self, body: dict[str, Any]) -> dict[str, Any]:
        payload = dict(body or {})
        return self._safe_operational_call(
            self._get_recipe_completion_exchange_service().import_package,
            filename=str(payload.get("filename") or ""),
            content_base64=str(payload.get("contenido_base64") or ""),
            expected_recipe_ids=(list(payload.get("recipe_ids") or []) if "recipe_ids" in payload else None),
            scope=str(payload.get("scope") or "BIBLIOTECA"),
            import_id=str(payload.get("import_id") or ""),
            source=str(payload.get("origen_propuesta") or "ARCHIVO_EXTERNO"),
        )

    def _safe_operational_call(self, operation: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
        try: return {**self._base_payload(), **operation(*args, **kwargs)}
        except (StockLoteWriteError, StockAjusteError, EscandalloEditorError, RecetaDocumentacionError, ArticuloDocumentacionError, PrecioReferenciaWebError) as exc:
            status = 403 if exc.code == "unauthorized" else 404 if exc.code.endswith("not_found") else 409 if "preview" in exc.code or "overwrite" in exc.code else 422
            error = self._error_payload(code=exc.code, message=str(exc)); error["error"]["status"] = status; return error

    def biblioteca(self) -> dict[str, Any]:
        return self._library_call(self._get_biblioteca_service().resumen)

    def elaboraciones(self, query: dict[str, Any]) -> dict[str, Any]:
        return self._library_call(self._get_biblioteca_service().listar, dict(query or {}))

    def elaboracion(self, elaboracion_id: str) -> dict[str, Any]:
        return self._library_call(self._get_biblioteca_service().detalle, elaboracion_id)

    def _get_yield_confirmation_service(self) -> ConfirmacionRendimientoElaboracionService:
        if self._yield_confirmation_service is None:
            self._yield_confirmation_service = ConfirmacionRendimientoElaboracionService(self.base_dir)
        return self._yield_confirmation_service

    def previsualizar_rendimiento_elaboracion(
        self, elaboracion_id: str, body: dict[str, Any], context: AuthorizedExecutionContext,
    ) -> dict[str, Any]:
        return self._yield_confirmation_call(
            self._get_yield_confirmation_service().preview,
            elaboracion_id, body, context,
        )

    def confirmar_rendimiento_elaboracion(
        self, elaboracion_id: str, body: dict[str, Any], context: AuthorizedExecutionContext,
    ) -> dict[str, Any]:
        return self._yield_confirmation_call(
            self._get_yield_confirmation_service().execute,
            elaboracion_id, body, context,
        )

    def _yield_confirmation_call(
        self, operation: Any, elaboracion_id: str, body: dict[str, Any],
        context: AuthorizedExecutionContext,
    ) -> dict[str, Any]:
        payload = dict(body or {})
        try:
            result = operation(
                escandallo_id=elaboracion_id,
                cantidad=payload.get("cantidad"),
                unidad=str(payload.get("unidad") or ""),
                modo=str(payload.get("modo") or "TOTAL"),
                propuesta_origen=str(payload.get("propuesta_origen") or "MANUAL"),
                origen={"tipo": "USUARIO", "referencia": payload.get("referencia")},
                context=context,
                **({
                    "preview_token": str(payload.get("preview_token") or ""),
                    "acepta_estimacion_parcial": payload.get("acepta_estimacion_parcial") is True,
                } if operation.__name__ == "execute" else {}),
            )
            return {**self._base_payload(), **result}
        except ErrorConfirmacionRendimiento as exc:
            status = 403 if exc.code == "unauthorized" else 404 if exc.code == "escandallo_not_found" else 409 if exc.code == "stale_or_invalid_preview" else 422
            error = self._error_payload(code=exc.code, message=str(exc))
            error["error"]["status"] = status
            return error
        except Exception:
            logger.exception("Error al confirmar el rendimiento de una elaboracion.")
            return self._error_payload(
                code="yield_confirmation_failed",
                message="No se pudo guardar el rendimiento.",
            )

    def _get_menus_service(self) -> MenusInteligentesService:
        if self._menus_service is None:
            self._menus_service = MenusInteligentesService(self.base_dir)
        return self._menus_service

    def menus(self, query: dict[str, Any]) -> dict[str, Any]:
        return self._library_call(self._get_menus_service().listar, dict(query or {}))

    def menu(self, menu_id: str) -> dict[str, Any]:
        return self._library_call(self._get_menus_service().obtener, menu_id)

    def elaboraciones_menu(self, query: dict[str, Any]) -> dict[str, Any]:
        return self._library_call(self._get_menus_service().elaboraciones, dict(query or {}))

    def crear_menu(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._library_call(self._get_menus_service().crear, dict(body or {}))

    def actualizar_menu(self, menu_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self._library_call(self._get_menus_service().actualizar, menu_id, dict(body or {}))

    def archivar_menu(self, menu_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self._library_call(self._get_menus_service().archivar, menu_id, dict(body or {}))

    def _get_menu_needs_service(self) -> MenuNecesidadesService:
        if self._menu_needs_service is None:
            self._menu_needs_service = MenuNecesidadesService(
                self.base_dir,
                compras=self._get_core().compras,
                stock_motor=self._get_core().stock,
            )
        return self._menu_needs_service

    def necesidades_menu(self, menu_id: str) -> dict[str, Any]:
        return self._library_call(self._get_menu_needs_service().necesidades, menu_id)

    def crear_propuesta_compra_menu(self, menu_id: str) -> dict[str, Any]:
        return self._library_call(self._get_menu_needs_service().crear_propuesta_con_pedidos, menu_id)

    def propuesta_compra_menu(self, menu_id: str, proposal_id: str) -> dict[str, Any]:
        return self._library_call(
            self._get_menu_needs_service().obtener_propuesta, menu_id, proposal_id
        )

    def actualizar_propuesta_compra_menu(self, menu_id: str, proposal_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self._library_call(self._get_menu_needs_service().actualizar_propuesta, menu_id, proposal_id, body)

    def crear_pedidos_propuesta_menu(self, menu_id: str, proposal_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self._library_call(self._get_menu_needs_service().crear_pedidos, menu_id, proposal_id, body)

    def _get_menu_production_service(self) -> MenuProduccionService:
        if self._menu_production_service is None:
            self._menu_production_service = MenuProduccionService(
                self._get_core(), necesidades=self._get_menu_needs_service()
            )
        return self._menu_production_service

    def crear_plan_produccion_menu(self, menu_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_menu_production_service().generar(menu_id, body)}

    def plan_produccion(self, plan_id: str) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_menu_production_service().obtener(plan_id)}

    def crear_propuesta_compra_produccion(self, plan_id: str) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_menu_production_service().crear_propuesta_compra(plan_id)}

    def revision_stock_produccion(self, plan_id: str) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_menu_production_service().revisar_stock(plan_id)}

    def registrar_stock_desde_produccion(self, plan_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_menu_production_service().registrar_inventario_desde_revision(plan_id, body)}

    def relacionar_articulo_produccion(self, plan_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_menu_production_service().relacionar_articulo(plan_id, body)}

    def _get_compras_drafts_service(self) -> ComprasBorradoresService:
        if self._compras_drafts_service is None:
            self._compras_drafts_service = ComprasBorradoresService(self._get_core().compras, self.base_dir)
        return self._compras_drafts_service

    def borrador_compra(self, pedido_id: str) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_compras_drafts_service().obtener(pedido_id)}

    def crear_borrador_compra_manual(self, body: dict[str, Any]) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_compras_drafts_service().crear_manual(body)}

    def actualizar_borrador_compra(self, pedido_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_compras_drafts_service().actualizar(pedido_id, body)}

    def confirmar_borrador_compra(self, pedido_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_compras_drafts_service().confirmar(pedido_id, body)}

    def _get_compras_receptions_service(self) -> ComprasRecepcionesService:
        if self._compras_receptions_service is None:
            self._compras_receptions_service = ComprasRecepcionesService(self._get_core())
        return self._compras_receptions_service

    def crear_recepcion_compra(self, pedido_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_compras_receptions_service().crear(pedido_id, body)}

    def recepcion_compra(self, reception_id: str) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_compras_receptions_service().obtener(reception_id)}

    def actualizar_recepcion_compra(self, reception_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_compras_receptions_service().actualizar(reception_id, body)}

    def confirmar_recepcion_compra(self, reception_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_compras_receptions_service().confirmar(reception_id, body)}

    def adjuntar_documento_recepcion_compra(self, reception_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_compras_receptions_service().adjuntar_documento(reception_id, body)}

    def documento_recepcion_compra(self, reception_id: str) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_compras_receptions_service().obtener_documento(reception_id)}

    def quitar_documento_recepcion_compra(self, reception_id: str) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_compras_receptions_service().quitar_documento(reception_id)}

    def _get_compras_reception_extraction_service(self) -> ComprasRecepcionExtractionService:
        if self._compras_reception_extraction_service is None:
            self._compras_reception_extraction_service = ComprasRecepcionExtractionService(self._get_core())
        return self._compras_reception_extraction_service

    def analizar_documento_recepcion_compra(self, reception_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_compras_reception_extraction_service().analizar(reception_id, body)}

    def aplicar_extraccion_recepcion_compra(self, reception_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return {**self._base_payload(), **self._get_compras_reception_extraction_service().aplicar(reception_id, body)}

    def _get_biblioteca_import_service(self) -> ImportDocumentService:
        if self._biblioteca_import_service is None:
            self._biblioteca_import_service = ImportDocumentService(
                self.base_dir, persistent_sessions=True,
            )
        return self._biblioteca_import_service

    def importacion_biblioteca_activa(self) -> dict[str, Any]:
        return self._library_call(
            self._get_biblioteca_import_service().get_active_import,
            error_code="library_import_failed",
            operation_name="consultar la importación activa de Biblioteca",
        )

    def listar_importaciones_biblioteca(self) -> dict[str, Any]:
        return self._library_call(
            self._get_biblioteca_import_service().list_imports,
            error_code="library_import_failed",
            operation_name="listar las importaciones de Biblioteca",
        )

    def descartar_importacion_biblioteca(self, importacion_id: str) -> dict[str, Any]:
        return self._library_call(
            self._get_biblioteca_import_service().discard_import,
            importacion_id,
            error_code="library_import_failed",
            operation_name="descartar una importación de Biblioteca",
        )

    def completado_externo_activo_importacion(self, importacion_id: str) -> dict[str, Any]:
        return self._safe_operational_call(
            self._get_recipe_docs_batch_service().active_external,
            importacion_id,
        )

    def crear_importacion_biblioteca(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._library_call(
            self._get_biblioteca_import_service().import_document,
            dict(body or {}),
            error_code="library_import_failed",
            operation_name="crear una importación de Biblioteca",
        )

    def importacion_biblioteca(self, importacion_id: str) -> dict[str, Any]:
        result = self._library_call(
            self._get_biblioteca_import_service().get_import,
            importacion_id,
            error_code="library_import_failed",
            operation_name="consultar una importación de Biblioteca",
        )
        if result.get("ok") and isinstance(result.get("importacion"), dict):
            active = self._get_recipe_docs_batch_service().active_external(importacion_id)
            result["importacion"] = {
                **result["importacion"],
                "completado_recetas_activo": active.get("batch"),
            }
        return result

    def propuestas_importacion_biblioteca(self, importacion_id: str) -> dict[str, Any]:
        return self._library_call(
            self._get_biblioteca_import_service().get_proposals,
            importacion_id,
            error_code="library_import_failed",
            operation_name="consultar propuestas de una importación de Biblioteca",
        )

    def borrador_importacion_biblioteca(self, importacion_id: str) -> dict[str, Any]:
        return self._library_call(
            self._get_biblioteca_import_service().get_draft,
            importacion_id,
            error_code="library_import_failed",
            operation_name="consultar el borrador de una importación de Biblioteca",
        )

    def actualizar_borrador_importacion_biblioteca(
        self, importacion_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        return self._library_call(
            self._get_biblioteca_import_service().update_draft,
            importacion_id,
            dict(body or {}),
            error_code="library_import_failed",
            operation_name="actualizar el borrador de una importación de Biblioteca",
        )

    def confirmar_importacion_biblioteca(
        self, importacion_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        return self._library_call(
            self._get_biblioteca_import_service().confirm, importacion_id, dict(body or {}),
            error_code="library_import_confirmation_failed",
            operation_name="confirmar una importación de Biblioteca",
        )

    def previsualizar_canonicalizacion_legacy_importacion(
        self, importacion_id: str, body: dict[str, Any], context: AuthorizedExecutionContext
    ) -> dict[str, Any]:
        return self._library_call(
            self._get_biblioteca_import_service().preview_legacy_canonicalization,
            importacion_id, dict(body or {}), context,
            error_code="legacy_canonicalization_preview_failed",
            operation_name="previsualizar la actualización de elaboraciones existentes",
        )

    def confirmar_canonicalizacion_legacy_importacion(
        self, importacion_id: str, body: dict[str, Any], context: AuthorizedExecutionContext
    ) -> dict[str, Any]:
        return self._library_call(
            self._get_biblioteca_import_service().confirm_legacy_canonicalization,
            importacion_id, dict(body or {}), context,
            error_code="legacy_canonicalization_confirmation_failed",
            operation_name="confirmar la actualización de elaboraciones existentes",
        )

    def estado_importacion_biblioteca(self, importacion_id: str) -> dict[str, Any]:
        return self._library_call(
            self._get_biblioteca_import_service().get_status, importacion_id,
            error_code="library_import_failed",
            operation_name="consultar el estado de una importación de Biblioteca",
        )

    def historial_importacion_biblioteca(self, importacion_id: str) -> dict[str, Any]:
        return self._library_call(
            self._get_biblioteca_import_service().get_history, importacion_id,
            error_code="library_import_failed",
            operation_name="consultar el historial de una importación de Biblioteca",
        )

    def _library_call(
        self,
        operation: Any,
        *args: Any,
        error_code: str = "library_unavailable",
        operation_name: str = "consultar la Biblioteca",
    ) -> dict[str, Any]:
        try:
            return {**self._base_payload(), **operation(*args)}
        except Exception as exc:
            logger.exception("Error al %s.", operation_name)
            env_name = str(os.getenv("HOST_AI_API_ENV", "development")).strip().lower()
            message = (
                f"{type(exc).__name__}: {exc}"
                if env_name == "development"
                else "No se pudo consultar la Biblioteca Culinaria."
            )
            return self._error_payload(
                code=error_code,
                message=message,
            )
