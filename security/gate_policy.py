"""Fail-closed authorization policy for the Genesis Gate.

This module does NOT verify JWT signatures. Claims must come only from trusted
authentication middleware after signature, issuer, audience, and algorithm
validation. Never pass user-supplied JSON as claims.
"""
from collections.abc import Callable, Mapping
from typing import Any


def authorize_gate(
    claims: Mapping[str, Any] | None,
    *,
    required_scope: str,
    expected_issuer: str,
    expected_audience: str,
    now: float,
    is_revoked: Callable[[str], bool],
) -> bool:
    """Return True only when validated claims satisfy every gate condition."""
    if not isinstance(claims, Mapping):
        return False
    if not all(isinstance(value, str) and value for value in (
        required_scope, expected_issuer, expected_audience
    )):
        return False

    issuer = claims.get("iss")
    subject = claims.get("sub")
    token_id = claims.get("jti")
    audience = claims.get("aud")
    expires_at = claims.get("exp")
    not_before = claims.get("nbf", 0)

    if issuer != expected_issuer:
        return False
    if not isinstance(subject, str) or not subject.strip():
        return False
    if not isinstance(token_id, str) or not token_id.strip():
        return False
    if audience != expected_audience and not (
        isinstance(audience, list) and expected_audience in audience
    ):
        return False
    if isinstance(expires_at, bool) or not isinstance(expires_at, (int, float)):
        return False
    if expires_at <= now:
        return False
    if isinstance(not_before, bool) or not isinstance(not_before, (int, float)):
        return False
    if not_before > now:
        return False

    scopes = claims.get("scope", [])
    if isinstance(scopes, str):
        scopes = scopes.split()
    if not isinstance(scopes, (list, tuple, set)):
        return False
    if required_scope not in scopes:
        return False

    if not callable(is_revoked):
        return False
    try:
        if is_revoked(token_id):
            return False
    except Exception:
        return False

    return True
