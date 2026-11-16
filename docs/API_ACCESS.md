# Aurora API access

All protected routes require a signed OIDC JWT in the Authorization header:

`Authorization: Bearer <access-token>`

The API validates the token signature against the configured JWKS endpoint and validates issuer, audience, expiry, not-before (if present), and subject. Only RS256 and ES256 are accepted.

| Route | Required scope | Notes |
|---|---|---|
| GET /health | Public | Minimal service status and ledger-valid flag; no ledger metadata |
| GET /personas | Public | Returns the allow-listed persona registry |
| GET /search?q=... | well:read | Owner-scoped lexical retrieval |
| GET /records/{event_id} | well:read | Owner-scoped record lookup |
| POST /observations | well:write | Appends a sourced observation |
| POST /patterns | well:write | Appends a proposed pattern with provenance |
| POST /chat | well:chat | Requires explicit consent and a configured model adapter |
| WS /ws | well:read | Authenticated transport acknowledgement only; no model response |

A missing verifier returns 401; a missing scope returns 403; a missing model adapter returns 503. The persona registry does not grant privileges. Never send bearer tokens in query strings.
