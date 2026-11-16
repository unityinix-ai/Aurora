"""OIDC/JWKS JWT verification. No token or claim is trusted before signature validation."""
from __future__ import annotations

import asyncio
import os
from urllib.parse import urlsplit

import jwt
from jwt import PyJWKClient


class JWTVerifier:
    """Verify RS256/ES256 access tokens against a configured HTTPS JWKS endpoint."""

    def __init__(self, *, jwks_url: str, issuer: str, audience: str, leeway: int = 30):
        parsed = urlsplit(jwks_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("JWT_JWKS_URL must be an HTTPS URL")
        if not issuer.startswith("https://") or not audience.strip():
            raise ValueError("JWT_ISSUER must be HTTPS and JWT_AUDIENCE must be set")
        if isinstance(leeway, bool) or not 0 <= leeway <= 120:
            raise ValueError("JWT clock skew must be between 0 and 120 seconds")
        self.issuer = issuer
        self.audience = audience
        self.leeway = leeway
        self.jwks = PyJWKClient(jwks_url, cache_keys=True, lifespan=300)

    @classmethod
    def from_env(cls):
        names = ("JWT_JWKS_URL", "JWT_ISSUER", "JWT_AUDIENCE")
        values = [os.getenv(name, "").strip() for name in names]
        if not any(values):
            return None
        if not all(values):
            raise RuntimeError("JWT_JWKS_URL, JWT_ISSUER and JWT_AUDIENCE must all be configured")
        try:
            leeway = int(os.getenv("JWT_CLOCK_SKEW_SECONDS", "30"))
        except ValueError as exc:
            raise RuntimeError("JWT_CLOCK_SKEW_SECONDS must be an integer") from exc
        return cls(jwks_url=values[0], issuer=values[1], audience=values[2], leeway=leeway)

    async def __call__(self, token: str) -> dict:
        return await asyncio.to_thread(self._verify, token)

    def _verify(self, token: str) -> dict:
        signing_key = self.jwks.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            issuer=self.issuer,
            audience=self.audience,
            leeway=self.leeway,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject.strip():
            raise jwt.InvalidTokenError("missing subject")
        scopes = claims.get("scope", [])
        if isinstance(scopes, str):
            scopes = scopes.split()
        if not isinstance(scopes, list) or any(not isinstance(s, str) for s in scopes):
            raise jwt.InvalidTokenError("invalid scope claim")
        claims["scope"] = scopes
        return claims
