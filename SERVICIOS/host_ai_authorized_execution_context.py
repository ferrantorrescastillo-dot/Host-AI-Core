from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any


TOOL_READ_SCOPES = {
    "consultar_estado_stock": "stock:read",
    "consultar_produccion": "produccion:read",
    "consultar_compras_pendientes": "compras:read",
}


@dataclass(frozen=True)
class AuthorizedExecutionContext:
    request_id: str
    user_id: str
    tenant_id: str
    roles: tuple[str, ...]
    scopes: frozenset[str]

    def validate(self) -> tuple[bool, str]:
        if not self.request_id.strip():
            return False, "missing_request_id"
        if not self.user_id.strip():
            return False, "missing_identity"
        if not self.tenant_id.strip():
            return False, "missing_tenant"
        return True, ""

    @classmethod
    def from_internal_environment(
        cls, request_id: str, *, role: str, allow_local_default: bool = False,
    ) -> "AuthorizedExecutionContext":
        """Resolve the server-owned identity used by local first-party surfaces.

        Environment values are never sent to, or accepted from, the browser.  The
        local default is only selected when the whole internal-auth configuration
        is absent; a partial/misconfigured identity remains unauthorized.
        """
        user_id = str(os.getenv("HOST_AI_INTERNAL_USER_ID") or "").strip()
        tenant_id = str(os.getenv("HOST_AI_INTERNAL_TENANT_ID") or "").strip()
        internal_names = (
            "HOST_AI_INTERNAL_USER_ID", "HOST_AI_INTERNAL_TENANT_ID",
            "HOST_AI_INTERNAL_ROLES", "HOST_AI_INTERNAL_SCOPES",
        )
        internal_configuration_present = any(os.getenv(name) is not None for name in internal_names)

        def values(name: str) -> tuple[str, ...]:
            return tuple(value for value in str(os.getenv(name) or "").replace(",", " ").split() if value)

        roles = values("HOST_AI_INTERNAL_ROLES") or (str(role or "internal"),)
        scopes = frozenset(values("HOST_AI_INTERNAL_SCOPES"))
        if allow_local_default and not internal_configuration_present:
            user_id = tenant_id = "host-ai-local"
            scopes = frozenset({
                "reservas:preview", "reservas:write",
                "articulos:preview", "articulos:write",
                "recetas:preview", "recetas:write",
                "escandallos:preview", "escandallos:write",
                "eventos:preview", "eventos:write",
                "stock:preview", "stock:write",
            })
        return cls(str(request_id or "").strip(), user_id, tenant_id, roles, scopes)

    @classmethod
    def from_access_token(cls, access_token: Any, request_id: str) -> "AuthorizedExecutionContext":
        claims = dict(getattr(access_token, "claims", None) or {})
        user_id = str(getattr(access_token, "subject", None) or claims.get("sub") or "").strip()
        tenant_id = str(claims.get("tenant_id") or "").strip()
        roles_raw = claims.get("roles") or []
        if isinstance(roles_raw, str):
            roles_raw = roles_raw.split()
        scopes = frozenset(str(scope).strip() for scope in list(getattr(access_token, "scopes", None) or []) if str(scope).strip())
        return cls(
            request_id=str(request_id or "").strip(),
            user_id=user_id,
            tenant_id=tenant_id,
            roles=tuple(str(role).strip() for role in roles_raw if str(role).strip()),
            scopes=scopes,
        )


__all__ = ["AuthorizedExecutionContext", "TOOL_READ_SCOPES"]
