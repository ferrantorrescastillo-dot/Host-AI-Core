from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


class HostAITenantResolver:
    """Resuelve un tenant autenticado a una factoría de adapter permitida."""

    def __init__(self, tenants: dict[str, Path], adapter_factory: Callable[[Path], Any]) -> None:
        self._tenants = {str(key): Path(value).resolve() for key, value in tenants.items() if str(key).strip()}
        self._adapter_factory = adapter_factory
        self._cache: dict[str, Any] = {}

    def resolve(self, tenant_id: str) -> Any | None:
        key = str(tenant_id or "").strip()
        root = self._tenants.get(key)
        if root is None or not root.is_dir():
            return None
        if key not in self._cache:
            self._cache[key] = self._adapter_factory(root)
        return self._cache[key]


__all__ = ["HostAITenantResolver"]
