from __future__ import annotations

import logging
import asyncio
import time
from pathlib import Path

import pytest

from SERVICIOS.host_ai_agent_policy import HostAIAgentPolicy
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.host_ai_mcp_adapter import HostAIMCPAdapter, HostAIMCPError
from SERVICIOS.host_ai_mcp_auth import HostAIJWTTokenVerifier
from SERVICIOS.host_ai_mcp_tenants import HostAITenantResolver
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_executor import HostAIToolResult
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


class _TenantExecutor:
    def __init__(self, tenant: str) -> None:
        self.tenant = tenant
        self.calls = 0

    def execute_agent_read(self, tool_id, arguments, execution_context=None):
        self.calls += 1
        assert execution_context.tenant_id == self.tenant
        return HostAIToolResult(estado="OK", mensaje="ok", datos={"tenant_result": self.tenant}, tool_id=tool_id)


def _adapter(tenant: str) -> HostAIMCPAdapter:
    return HostAIMCPAdapter(
        HostAIToolCatalog(build_default_tool_registry()), _TenantExecutor(tenant), HostAIAgentPolicy(),
    )


def _context(tenant="A", scopes=("stock:read",), user="user-1"):
    return AuthorizedExecutionContext("REQ-1", user, tenant, ("chef",), frozenset(scopes))


def test_usuario_tenant_y_scope_validos_ejecutan_read() -> None:
    result = _adapter("A").call_tool(
        "consultar_estado_stock", {"consulta": "resumen"}, execution_context=_context(), require_auth=True,
    )
    assert result["structuredContent"]["datos"]["tenant_result"] == "A"
    assert result["structuredContent"]["datos_reales_modificados"] is False


@pytest.mark.parametrize("context", [None, _context(user=""), _context(tenant=""), _context(scopes=())])
def test_denegacion_por_identidad_tenant_o_scope_faltante(context) -> None:
    with pytest.raises(HostAIMCPError) as error:
        _adapter("A").call_tool(
            "consultar_estado_stock", {"consulta": "resumen"}, execution_context=context, require_auth=True,
        )
    assert error.value.code == "access_denied"


def test_tenant_se_deriva_del_contexto_y_no_de_argumentos() -> None:
    with pytest.raises(HostAIMCPError) as error:
        _adapter("A").call_tool(
            "consultar_estado_stock", {"consulta": "resumen", "tenant_id": "B"},
            execution_context=_context("A"), require_auth=True,
        )
    assert error.value.code == "invalid_arguments"


def test_resolver_no_permite_tenant_ajeno(tmp_path: Path) -> None:
    tenant_a = tmp_path / "A"; tenant_a.mkdir()
    resolver = HostAITenantResolver({"A": tenant_a}, lambda _path: _adapter("A"))
    assert resolver.resolve("A") is not None
    assert resolver.resolve("B") is None


def test_auditoria_saneada_incluye_contexto_sin_secretos(caplog) -> None:
    caplog.set_level(logging.INFO, logger="host_ai.mcp")
    _adapter("A").call_tool(
        "consultar_estado_stock", {"consulta": "resumen"}, request_id="REQ-AUDIT",
        execution_context=_context(), require_auth=True,
    )
    text = caplog.text
    assert "REQ-AUDIT" in text and "user-1" in text and "stock:read" in text
    assert "access_token" not in text and "Bearer " not in text and "tenant_result" not in text


def test_verificador_jwt_acepta_token_valido_y_rechaza_invalido() -> None:
    import jwt
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    verifier = HostAIJWTTokenVerifier(
        issuer="https://auth.example.test", audience="https://mcp.example.test", public_key=public_key,
    )
    now = int(time.time())
    claims = {
        "iss": "https://auth.example.test", "aud": "https://mcp.example.test",
        "sub": "user-1", "tenant_id": "A", "scope": "stock:read", "roles": ["chef"],
        "iat": now, "exp": now + 300,
    }
    token = jwt.encode(claims, private_key, algorithm="RS256")
    verified = asyncio.run(verifier.verify_token(token))
    assert verified is not None
    assert verified.subject == "user-1" and verified.claims["tenant_id"] == "A"
    assert verified.scopes == ["stock:read"]
    assert asyncio.run(verifier.verify_token(token + "alterado")) is None


def test_verificador_jwks_normaliza_claims_con_namespace_sin_red() -> None:
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    class _SigningKey:
        key = private_key.public_key()

    class _JWKSClient:
        def __init__(self) -> None:
            self.tokens: list[str] = []

        def get_signing_key_from_jwt(self, token: str):
            self.tokens.append(token)
            return _SigningKey()

    tenant_claim = "https://host-ai.example/tenant_id"
    roles_claim = "https://host-ai.example/roles"
    jwks_client = _JWKSClient()
    verifier = HostAIJWTTokenVerifier(
        issuer="https://tenant.eu.auth0.com/", audience="https://mcp.example.test",
        jwks_url="https://tenant.eu.auth0.com/.well-known/jwks.json",
        tenant_claim=tenant_claim, roles_claim=roles_claim, jwks_client=jwks_client,
    )
    now = int(time.time())
    token = jwt.encode({
        "iss": "https://tenant.eu.auth0.com/", "aud": "https://mcp.example.test",
        "sub": "auth0|user-1", tenant_claim: "restaurant-dev",
        roles_claim: ["chef"], "scope": "stock:read", "iat": now, "exp": now + 300,
    }, private_key, algorithm="RS256", headers={"kid": "dev-key"})

    verified = asyncio.run(verifier.verify_token(token))

    assert verified is not None
    assert verified.claims["tenant_id"] == "restaurant-dev"
    assert verified.claims["roles"] == ["chef"]
    assert verified.scopes == ["stock:read"]
    assert jwks_client.tokens == [token]
