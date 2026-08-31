from __future__ import annotations

import asyncio
import logging
import os
import json
from pathlib import Path
from typing import Any

from CORE.host_ai_core import HostAICore
from SERVICIOS.host_ai_agent_policy import HostAIAgentPolicy
from SERVICIOS.host_ai_home_read_service import HostAIHomeReadService
from SERVICIOS.host_ai_mcp_adapter import HostAIMCPAdapter, HostAIMCPError
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.host_ai_mcp_auth import HostAIJWTTokenVerifier
from SERVICIOS.host_ai_mcp_tenants import HostAITenantResolver
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


LOGGER = logging.getLogger("host_ai.mcp.server")
LOCAL_DEV_NOTICE = "HOST AI MCP LOCAL DEV ONLY - READ ONLY"
REMOTE_DEV_NOTICE = "HOST AI MCP REMOTE DEV - OAUTH RESOURCE SERVER - READ ONLY"


def build_adapter(base_dir: Path | None = None) -> HostAIMCPAdapter:
    root = Path(base_dir or Path.cwd()).resolve()
    core = HostAICore(root)
    home = HostAIHomeReadService(core)
    registry = build_default_tool_registry()
    return HostAIMCPAdapter(
        HostAIToolCatalog(registry),
        HostAIToolExecutor(registry, home_read_service=home),
        HostAIAgentPolicy(),
    )


def build_server(adapter: HostAIMCPAdapter | None = None) -> Any:
    try:
        from mcp.server import Server
        from mcp.types import CallToolResult, TextContent, Tool, ToolAnnotations
    except ImportError as exc:
        raise RuntimeError("MCP SDK is not installed. Install API/requirements-http.txt.") from exc

    read_adapter = adapter or build_adapter()
    server = Server("host-ai-local-read")

    @server.list_tools()
    async def list_tools() -> list[Any]:
        return [
            Tool(
                name=item["name"],
                description=item["description"],
                inputSchema=item["inputSchema"],
                outputSchema=item["outputSchema"],
                annotations=ToolAnnotations(**item["annotations"]),
            )
            for item in read_adapter.list_tools()
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None) -> Any:
        try:
            payload = read_adapter.call_tool(name, arguments)
        except HostAIMCPError as exc:
            return CallToolResult(
                content=[TextContent(type="text", text=exc.public_message)],
                isError=True,
            )
        return CallToolResult(
            content=[TextContent(**item) for item in payload["content"]],
            structuredContent=payload["structuredContent"],
            isError=bool(payload["isError"]),
        )

    return server


def build_remote_server(
    *,
    tenant_resolver: HostAITenantResolver,
    token_verifier: Any,
    issuer_url: str,
    resource_server_url: str,
    host: str = "127.0.0.1",
    port: int = 8001,
) -> Any:
    from mcp.server.auth.middleware.auth_context import get_access_token
    from mcp.server.auth.settings import AuthSettings
    from mcp.server.fastmcp import FastMCP
    from mcp.types import CallToolResult, TextContent, Tool, ToolAnnotations

    remote = FastMCP(
        "host-ai-remote-read",
        instructions=REMOTE_DEV_NOTICE,
        token_verifier=token_verifier,
        auth=AuthSettings(
            issuer_url=issuer_url,
            resource_server_url=resource_server_url,
            required_scopes=[],
        ),
        host=host,
        port=port,
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
    )
    protocol = remote._mcp_server

    @protocol.list_tools()
    async def list_tools() -> list[Any]:
        access_token = get_access_token()
        context = AuthorizedExecutionContext.from_access_token(access_token, "MCP-LIST") if access_token else None
        if context is None or not context.validate()[0] or tenant_resolver.resolve(context.tenant_id) is None:
            return []
        adapter = tenant_resolver.resolve(context.tenant_id)
        return [
            Tool(
                name=item["name"], description=item["description"], inputSchema=item["inputSchema"],
                outputSchema=item["outputSchema"], annotations=ToolAnnotations(**item["annotations"]),
            )
            for item in adapter.list_tools()
        ]

    @protocol.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None) -> Any:
        access_token = get_access_token()
        request_id = f"MCP-{os.urandom(12).hex()}"
        context = AuthorizedExecutionContext.from_access_token(access_token, request_id) if access_token else None
        adapter = tenant_resolver.resolve(context.tenant_id) if context else None
        if adapter is None:
            return CallToolResult(content=[TextContent(type="text", text="MCP request rejected: invalid tenant.")], isError=True)
        try:
            payload = adapter.call_tool(name, arguments, request_id=request_id, execution_context=context, require_auth=True)
        except HostAIMCPError as exc:
            return CallToolResult(content=[TextContent(type="text", text=exc.public_message)], isError=True)
        return CallToolResult(
            content=[TextContent(**item) for item in payload["content"]],
            structuredContent=payload["structuredContent"], isError=bool(payload["isError"]),
        )

    return remote


def build_remote_http_app(remote_server: Any) -> Any:
    from mcp.server.auth.routes import create_protected_resource_routes
    from pydantic import AnyHttpUrl
    from starlette.applications import Starlette
    from starlette.routing import Mount

    inner = remote_server.streamable_http_app()
    resource_url = AnyHttpUrl(str(remote_server.settings.auth.resource_server_url))
    issuer_url = AnyHttpUrl(str(remote_server.settings.auth.issuer_url))
    metadata_routes = create_protected_resource_routes(
        resource_url=resource_url,
        authorization_servers=[issuer_url],
        scopes_supported=["stock:read", "produccion:read", "compras:read"],
        resource_name="HOST AI Read-only MCP",
    )
    inner.router.routes = [
        route for route in inner.routes
        if not str(getattr(route, "path", "")).startswith("/.well-known/oauth-protected-resource")
    ]
    return Starlette(routes=[*metadata_routes, Mount("/", app=inner)], lifespan=inner.router.lifespan_context)


def build_remote_server_from_env() -> Any:
    issuer = str(os.getenv("HOST_AI_MCP_OAUTH_ISSUER") or "").strip()
    resource = str(os.getenv("HOST_AI_MCP_RESOURCE_URL") or "").strip()
    public_key_path = str(os.getenv("HOST_AI_MCP_OAUTH_PUBLIC_KEY_FILE") or "").strip()
    jwks_url = str(os.getenv("HOST_AI_MCP_OAUTH_JWKS_URL") or "").strip()
    tenant_map_raw = str(os.getenv("HOST_AI_MCP_TENANTS_JSON") or "").strip()
    if not issuer or not resource or not tenant_map_raw or bool(public_key_path) == bool(jwks_url):
        raise RuntimeError("Remote MCP OAuth/tenant configuration is incomplete.")
    tenant_map = json.loads(tenant_map_raw)
    if not isinstance(tenant_map, dict):
        raise RuntimeError("HOST_AI_MCP_TENANTS_JSON must be an object.")
    resolver = HostAITenantResolver({str(key): Path(value) for key, value in tenant_map.items()}, build_adapter)
    verifier_options = {
        "issuer": issuer,
        "audience": resource,
        "algorithm": str(os.getenv("HOST_AI_MCP_OAUTH_ALGORITHM") or "RS256"),
    }
    if jwks_url:
        verifier = HostAIJWTTokenVerifier.from_jwks(
            **verifier_options, jwks_url=jwks_url,
            tenant_claim=str(os.getenv("HOST_AI_MCP_TENANT_CLAIM") or "tenant_id"),
            roles_claim=str(os.getenv("HOST_AI_MCP_ROLES_CLAIM") or "roles"),
        )
    else:
        verifier = HostAIJWTTokenVerifier.from_public_key_file(
            **verifier_options, public_key_path=Path(public_key_path),
        )
    return build_remote_server(
        tenant_resolver=resolver, token_verifier=verifier, issuer_url=issuer,
        resource_server_url=resource,
        host=str(os.getenv("HOST_AI_MCP_HOST") or "127.0.0.1"),
        port=int(os.getenv("HOST_AI_MCP_PORT") or "8001"),
    )


async def _run_stdio() -> None:
    from mcp.server.stdio import stdio_server

    server = build_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> int:
    if str(os.getenv("HOST_AI_MCP_ENABLED") or "").strip() != "1":
        LOGGER.error("MCP disabled. Set HOST_AI_MCP_ENABLED=1 for local development only.")
        return 2
    logging.basicConfig(level=logging.INFO)
    transport = str(os.getenv("HOST_AI_MCP_TRANSPORT") or "stdio").strip().lower()
    if transport == "streamable-http":
        LOGGER.warning(REMOTE_DEV_NOTICE)
        import uvicorn

        remote = build_remote_server_from_env()
        uvicorn.run(
            build_remote_http_app(remote), host=remote.settings.host, port=remote.settings.port,
            log_level=remote.settings.log_level.lower(),
        )
    elif transport == "stdio":
        LOGGER.warning(LOCAL_DEV_NOTICE)
        asyncio.run(_run_stdio())
    else:
        LOGGER.error("Unsupported MCP transport.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "LOCAL_DEV_NOTICE", "REMOTE_DEV_NOTICE", "build_adapter", "build_server",
    "build_remote_server", "build_remote_http_app", "build_remote_server_from_env", "main",
]
