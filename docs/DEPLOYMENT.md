# Aurora staging deployment

This repository now contains a containerized FastAPI API and a Caddy HTTPS reverse-proxy template. It is a deployment template, not a deployed environment.

## Required external decisions and resources

1. A Linux staging host with Docker Engine and the Docker Compose plugin.
2. A DNS name whose A/AAAA records point to that host; inbound TCP 80/443 must reach Caddy.
3. An OIDC identity provider that issues JWT access tokens and publishes an HTTPS JWKS endpoint.
4. The provider's exact issuer URL, API audience, and JWKS URL.
5. If chat is to be enabled, a model provider account, API key, and model identifier.

No identity provider, cloud host, DNS zone, or model account is selected by this repository. Do not invent these values or place real credentials in Git.

## Authentication contract

The API verifies bearer JWTs using the configured JWKS and permits only RS256 or ES256. It checks signature, issuer, audience, expiration, not-before (when present), and subject. JWKS keys are cached and refreshed by PyJWT's JWKS client. Tokens must carry scopes:
- `well:read` for search, record reads, and WebSocket transport.
- `well:write` for observations and patterns.
- `well:chat` for model requests.

Configure the OIDC application to issue these scopes only to authorized users. The API does not accept identity claims supplied by the browser or model. Missing authentication configuration leaves private routes closed. Partial or malformed authentication configuration aborts startup.

The current implementation does not provide token revocation/introspection or a user sign-in UI. Use short-lived access tokens and configure the frontend's OIDC client separately before exposing a browser application. Do not place bearer tokens in URLs or localStorage.

## Model provider

Set `MODEL_API_KEY`, `MODEL_NAME`, and optionally `MODEL_API_BASE_URL` on the host. The adapter uses an OpenAI-compatible `/chat/completions` endpoint over HTTPS. Without both key and model name, chat returns 503 while the non-chat API can still run. The provider receives the user message and retrieved evidence; ensure the provider's data handling terms meet your requirements.

## Host setup

1. Provision the host and DNS; restrict SSH and firewall access to required administration sources.
2. Install Docker Engine and Docker Compose using the host OS vendor's official instructions.
3. Copy this repository to the host at a pinned reviewed commit.
4. Copy `.env.example` to `.env`, replace every example value with the real provider/domain values, and set restrictive file permissions (for example, `chmod 600 .env`).
5. Ensure the OIDC issuer, audience, and JWKS URL exactly match the identity provider configuration. Ensure the frontend origin is listed in `CORS_ORIGINS`.
6. Run `docker compose config` and review the rendered configuration locally on the host. Do not paste secrets into tickets or logs.
7. Run `docker compose up --build -d`; confirm `docker compose ps`, `docker compose logs --tail=100 api caddy`, and `https://$DOMAIN/health`.
8. Confirm the health response reports valid ledger integrity and authentication configuration. Chat should report model configuration only after a provider key and model are supplied.
9. Configure platform-level rate limiting, alerting, host patching, encrypted off-host backups, and a tested restore process before real user data is stored.

## Operational controls and known gaps

- API container runs as non-root, drops Linux capabilities, uses a read-only root filesystem, and persists only the SQLite data volume.
- Caddy terminates TLS and adds baseline security headers. Certificate issuance requires valid DNS and reachable ports 80/443.
- CORS is an explicit origin allow-list; trusted hosts are constrained to the configured domain and local health-check hosts.
- SQLite and the SHA-256 event chain are not a substitute for encrypted backups, access-controlled storage, signed external checkpoints, or disaster-recovery tests.
- No distributed rate limiter, token revocation service, audit-log export, monitoring/alerting integration, or independent security assessment is included yet. Do not expose the service publicly until those controls are supplied by the hosting platform or added and tested.
- The React frontend is not bundled into this API image. Host it separately over HTTPS, set its API URL to this deployment, configure its OIDC sign-in flow, and add its exact origin to `CORS_ORIGINS`.

## Local checks

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
docker build -t aurora-api:staging .
```

CI validates unit tests and builds the container image. CI success does not deploy the service or prove production security.
