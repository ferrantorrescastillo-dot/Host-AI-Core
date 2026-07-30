from __future__ import annotations

from pathlib import Path
from typing import Any

from API.facade.core_public_api02 import CorePublicApi02Facade
from SERVICIOS.articulos_catalog_read_service import ArticulosCatalogReadService
from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService
from SERVICIOS.importador_inteligente_biblioteca import ImportDocumentService


class CatalogPublicFacade(CorePublicApi02Facade):
    """Amplía la fachada certificada con consultas de catálogo de solo lectura."""

    def __init__(self, base_dir: Path | None = None) -> None:
        super().__init__(base_dir=base_dir)
        self._articulos_service: ArticulosCatalogReadService | None = None
        self._biblioteca_service: BibliotecaCulinariaReadService | None = None
        self._biblioteca_import_service: ImportDocumentService | None = None

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

    def _get_biblioteca_import_service(self) -> ImportDocumentService:
        if self._biblioteca_import_service is None:
            self._biblioteca_import_service = ImportDocumentService(self.base_dir)
        return self._biblioteca_import_service

    def crear_importacion_biblioteca(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._library_call(
            self._get_biblioteca_import_service().import_document, dict(body or {})
        )

    def importacion_biblioteca(self, importacion_id: str) -> dict[str, Any]:
        return self._library_call(
            self._get_biblioteca_import_service().get_import, importacion_id
        )

    def propuestas_importacion_biblioteca(self, importacion_id: str) -> dict[str, Any]:
        return self._library_call(
            self._get_biblioteca_import_service().get_proposals, importacion_id
        )

    def _library_call(self, operation: Any, *args: Any) -> dict[str, Any]:
        try:
            return {**self._base_payload(), **operation(*args)}
        except Exception:
            return self._error_payload(
                code="library_unavailable",
                message="No se pudo consultar la Biblioteca Culinaria.",
            )
