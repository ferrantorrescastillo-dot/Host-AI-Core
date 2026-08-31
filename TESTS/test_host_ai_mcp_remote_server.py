from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from SERVICIOS.host_ai_mcp_server import build_remote_http_app, build_remote_server
from SERVICIOS.host_ai_mcp_tenants import HostAITenantResolver


class _Verifier:
    async def verify_token(self, token):
        return None


def test_remote_server_es_streamable_http_local_con_auth(tmp_path: Path) -> None:
    tenant = tmp_path / "A"; tenant.mkdir()
    resolver = HostAITenantResolver({"A": tenant}, lambda _path: object())
    server = build_remote_server(
        tenant_resolver=resolver,
        token_verifier=_Verifier(),
        issuer_url="https://auth.example.test",
        resource_server_url="https://mcp.example.test",
    )
    assert server.settings.host == "127.0.0.1"
    assert server.settings.streamable_http_path == "/mcp"
    assert server.settings.auth is not None
    app = server.streamable_http_app()
    assert any(getattr(route, "path", "") == "/mcp" for route in app.routes)


def test_http_remoto_rechaza_token_invalido_y_publica_scopes(tmp_path: Path) -> None:
    tenant = tmp_path / "A"; tenant.mkdir()
    resolver = HostAITenantResolver({"A": tenant}, lambda _path: object())
    server = build_remote_server(
        tenant_resolver=resolver, token_verifier=_Verifier(), issuer_url="https://auth.example.test",
        resource_server_url="https://mcp.example.test",
    )
    with TestClient(build_remote_http_app(server)) as client:
        assert client.get("/mcp").status_code == 401
        assert client.get("/mcp", headers={"Authorization": "Bearer invalid"}).status_code == 401
        metadata = client.get("/.well-known/oauth-protected-resource")
        assert metadata.status_code == 200
        assert metadata.json()["scopes_supported"] == ["stock:read", "produccion:read", "compras:read"]
