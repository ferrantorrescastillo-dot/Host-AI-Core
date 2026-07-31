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


logger = logging.getLogger(__name__)


class CatalogPublicFacade(CorePublicApi02Facade):
    """Amplía la fachada certificada con consultas de catálogo de solo lectura."""

    def __init__(self, base_dir: Path | None = None) -> None:
        super().__init__(base_dir=base_dir)
        self._articulos_service: ArticulosCatalogReadService | None = None
        self._biblioteca_service: BibliotecaCulinariaReadService | None = None
        self._biblioteca_import_service: ImportDocumentService | None = None
        self._menus_service: MenusInteligentesService | None = None

    def _get_articulos_service(self) -> ArticulosCatalogReadService:
        if self._articulos_service is None:
            self._articulos_service = ArticulosCatalogReadService(
                self.base_dir,
                stock=self._get_core().stock,
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

    def _get_biblioteca_service(self) -> BibliotecaCulinariaReadService:
        if self._biblioteca_service is None:
            self._biblioteca_service = BibliotecaCulinariaReadService(self.base_dir)
        return self._biblioteca_service

    def biblioteca(self) -> dict[str, Any]:
        return self._library_call(self._get_biblioteca_service().resumen)

    def elaboraciones(self, query: dict[str, Any]) -> dict[str, Any]:
        return self._library_call(self._get_biblioteca_service().listar, dict(query or {}))

    def elaboracion(self, elaboracion_id: str) -> dict[str, Any]:
        return self._library_call(self._get_biblioteca_service().detalle, elaboracion_id)

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

    def _get_biblioteca_import_service(self) -> ImportDocumentService:
        if self._biblioteca_import_service is None:
            self._biblioteca_import_service = ImportDocumentService(self.base_dir)
        return self._biblioteca_import_service

    def crear_importacion_biblioteca(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._library_call(
            self._get_biblioteca_import_service().import_document,
            dict(body or {}),
            error_code="library_import_failed",
            operation_name="crear una importación de Biblioteca",
        )

    def importacion_biblioteca(self, importacion_id: str) -> dict[str, Any]:
        return self._library_call(
            self._get_biblioteca_import_service().get_import,
            importacion_id,
            error_code="library_import_failed",
            operation_name="consultar una importación de Biblioteca",
        )

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
