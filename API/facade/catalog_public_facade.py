from __future__ import annotations

from pathlib import Path
from typing import Any

from API.facade.core_public_api02 import CorePublicApi02Facade
from SERVICIOS.articulos_catalog_read_service import ArticulosCatalogReadService


class CatalogPublicFacade(CorePublicApi02Facade):
    """Amplía la fachada certificada con consultas de catálogo de solo lectura."""

    def __init__(self, base_dir: Path | None = None) -> None:
        super().__init__(base_dir=base_dir)
        self._articulos_service: ArticulosCatalogReadService | None = None

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
