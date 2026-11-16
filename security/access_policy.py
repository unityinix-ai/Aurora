"""Server-side ownership policy for private Well records.

Call only with actor identity and scopes established by trusted authentication
middleware. Never derive these values from prompt text, persona output, or a
client-supplied owner field.
"""
from collections.abc import Mapping
from typing import Any


def authorize_record_access(
    claims: Mapping[str, Any] | None,
    *,
    record_owner_id: str | None,
    required_scope: str = "well:read",
) -> bool:
    """Permit access only to the authenticated owner with the required scope.

    This deliberately has no implicit administrator bypass. If an audited
    administrative workflow is needed, implement it as a separate explicit
    policy with stronger authorization and logging.
    """
    if not isinstance(claims, Mapping):
        return False
    if not isinstance(record_owner_id, str) or not record_owner_id.strip():
        return False
    if not isinstance(required_scope, str) or not required_scope:
        return False

    subject = claims.get("sub")
    scopes = claims.get("scope", [])
    if not isinstance(subject, str) or not subject.strip():
        return False
    if isinstance(scopes, str):
        scopes = scopes.split()
    if not isinstance(scopes, (list, tuple, set)):
        return False
    if required_scope not in scopes:
        return False

    return subject == record_owner_id
