from __future__ import annotations

from typing import Any


class CorePublicStubFacade:
    """Implementacion temporal para API-01.

    No ejecuta logica de negocio.
    Solo devuelve contratos estables para cableado inicial de rutas.
    """

    def _pending(self, endpoint: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        data = {
            "ok": True,
            "estado": "PENDING_API_02",
            "endpoint": endpoint,
            "mensaje": "Fachada definida. Integracion funcional pendiente en API-02.",
            "datos_reales_modificados": False,
        }
        if extra:
            data.update(extra)
        return data

    def health(self) -> dict[str, Any]:
        return {
            "ok": True,
            "service": "HOST_AI_PLATFORM_API",
            "estado": "UP",
            "version": "API-01",
            "core_modificado": False,
            "datos_reales_modificados": False,
        }

    def version(self) -> dict[str, Any]:
        return {
            "ok": True,
            "platform_api_version": "API-01",
            "core_version_target": "Host AI Core 1.0 (congelado)",
            "datos_reales_modificados": False,
        }

    def executive(self, query: dict[str, Any]) -> dict[str, Any]:
        return self._pending("GET /executive", {"query": dict(query or {})})

    def dashboard(self, query: dict[str, Any]) -> dict[str, Any]:
        return self._pending("GET /dashboard", {"query": dict(query or {})})

    def eventos(self, query: dict[str, Any]) -> dict[str, Any]:
        return self._pending("GET /eventos", {"query": dict(query or {})})

    def workflow(self, query: dict[str, Any]) -> dict[str, Any]:
        return self._pending("GET /workflow", {"query": dict(query or {})})

    def plan(self, query: dict[str, Any]) -> dict[str, Any]:
        return self._pending("GET /plan", {"query": dict(query or {})})

    def chat(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._pending("POST /chat", {"body": dict(body or {})})
