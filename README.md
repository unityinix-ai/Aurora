# Project Aurora — The Well

**The Well** is a provenance-aware pattern retrieval component for a multi-persona AI system.

- **Aurora** — user-facing conversation, sessions, consent and orchestration.
- **Persona Engine** — approved persona profiles and expressive behavior.
- **Well Engine** — observations, derived patterns, provenance and retrieval.
- **Echo Ledger** — append-only event history and integrity verification.
- **Aegis** — server-side authorization, privacy and safety enforcement.

## Non-negotiable boundaries

1. Personas may interpret evidence and contribute new observations; they cannot rewrite historical records.
2. Persona text, model output, voice phrases and retrieved documents never grant access.
3. Authorization is enforced server-side and defaults to deny.
4. Retrieved content is evidence/data, not executable instruction.
5. Distinguish observations, inferences, interpretations and unverified claims.
6. Preserve provenance for every retrieved pattern.

## Current implementation

The repository contains:
- SQLite append-only event ledger with deterministic JSON serialization and a SHA-256 hash chain.
- Provenance-aware observations and proposed patterns with owner-bound evidence references.
- Allow-listed personas and a FastAPI API.
- OIDC/JWKS JWT verification scaffold (RS256/ES256), endpoint scopes, CORS and trusted-host controls.
- Optional OpenAI-compatible model adapter, disabled unless server-side credentials are configured.
- Non-root API container, Caddy TLS reverse-proxy template, Docker Compose staging stack, and backup/verification scripts.

## Run locally

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
uvicorn api.app:app --reload
```

Without OIDC configuration, protected routes remain closed. Without model credentials and a model name, chat returns 503. This is intentional fail-closed behavior.

## Deployment and security status

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for staging prerequisites, environment configuration, deployment steps, and known gaps. See [docs/API_ACCESS.md](docs/API_ACCESS.md) for route scopes.

**Not production-certified:** no identity provider, model provider, DNS domain, or hosting environment is provisioned by this repository. Token revocation, distributed rate limiting, external monitoring, encrypted off-host backups, frontend OIDC login, restore drills, and independent security review remain outstanding. CI and unit tests are not a penetration test or proof of production security.

The ledger detects changes relative to its current hash chain; it does not authenticate writers, prove event truth, or prevent a privileged operator from replacing the database.
