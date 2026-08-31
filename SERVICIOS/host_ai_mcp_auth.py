from __future__ import annotations

from pathlib import Path
from typing import Any


class HostAIJWTTokenVerifier:
    """Verifica JWT OAuth firmados; no emite tokens ni almacena credenciales."""

    def __init__(
        self, *, issuer: str, audience: str, public_key: str | None = None,
        jwks_url: str | None = None, algorithm: str = "RS256",
        tenant_claim: str = "tenant_id", roles_claim: str = "roles",
        jwks_client: Any | None = None,
    ) -> None:
        if not issuer or not audience or (not public_key and not jwks_url):
            raise ValueError("OAuth verifier configuration is incomplete.")
        if public_key and jwks_url:
            raise ValueError("Configure either a public key or a JWKS URL, not both.")
        if not tenant_claim or not roles_claim:
            raise ValueError("OAuth claim configuration is incomplete.")
        if algorithm not in {"RS256", "RS384", "RS512", "ES256", "ES384"}:
            raise ValueError("OAuth signing algorithm is not allowed.")
        # `iss` y `aud` son identificadores exactos. Proveedores OIDC como Auth0
        # publican normalmente el issuer con barra final; normalizarlo rompería
        # la validación criptográfica de un token válido.
        self.issuer = issuer
        self.audience = audience
        self.public_key = public_key
        self.jwks_url = jwks_url
        self.algorithm = algorithm
        self.tenant_claim = tenant_claim
        self.roles_claim = roles_claim
        self._jwks_client = jwks_client

    async def verify_token(self, token: str) -> Any | None:
        try:
            import jwt
            from mcp.server.auth.provider import AccessToken

            verification_key = self.public_key
            if self.jwks_url:
                client = self._jwks_client or jwt.PyJWKClient(self.jwks_url)
                self._jwks_client = client
                verification_key = client.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                verification_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience,
                options={"require": ["exp", "iat", "iss", "aud", "sub", self.tenant_claim]},
            )
            raw_scope = claims.get("scope") or ""
            scopes = raw_scope.split() if isinstance(raw_scope, str) else list(raw_scope or [])
            return AccessToken(
                token="verified",
                client_id=str(claims.get("client_id") or claims.get("azp") or "chatgpt"),
                scopes=[str(scope) for scope in scopes],
                expires_at=int(claims["exp"]),
                resource=self.audience,
                subject=str(claims["sub"]),
                claims={
                    "sub": str(claims["sub"]),
                    "tenant_id": str(claims[self.tenant_claim]),
                    "roles": list(claims.get(self.roles_claim) or []),
                    "iss": str(claims["iss"]),
                },
            )
        except Exception:
            return None

    @classmethod
    def from_public_key_file(cls, *, issuer: str, audience: str, public_key_path: Path, algorithm: str = "RS256") -> "HostAIJWTTokenVerifier":
        return cls(issuer=issuer, audience=audience, public_key=Path(public_key_path).read_text(encoding="utf-8"), algorithm=algorithm)

    @classmethod
    def from_jwks(
        cls, *, issuer: str, audience: str, jwks_url: str, algorithm: str = "RS256",
        tenant_claim: str = "tenant_id", roles_claim: str = "roles",
    ) -> "HostAIJWTTokenVerifier":
        return cls(
            issuer=issuer, audience=audience, jwks_url=jwks_url, algorithm=algorithm,
            tenant_claim=tenant_claim, roles_claim=roles_claim,
        )


__all__ = ["HostAIJWTTokenVerifier"]
