# The Well — Operations
FastAPI entry point: api.app:app. Database path: WELL_DB, default well.sqlite3. The authenticator and model adapter intentionally default to unavailable. Protected endpoints deny requests until maintained OIDC/JWT verification and a reviewed model adapter are injected. Validate signatures, allowed algorithm, issuer, audience, expiry, not-before and key rotation. Never accept claims supplied by the browser or model. Do not place bearer tokens in URLs.

Local run:
    python -m pip install -r requirements.txt
    uvicorn api.app:app --reload
    python -m unittest discover -s tests -v
Frontend:
    cd frontend && npm install && npm run dev
Set VITE_API_URL at build time if API is not localhost:8000.

Backup with SQLite online backup API:
    python ops/backup_db.py well.sqlite3 backups/well-backup.sqlite3
    python ops/verify_db.py backups/well-backup.sqlite3
Restore in a maintenance window after stopping writers. Preserve original as rollback artifact, restore to a new path, verify SQLite integrity and hash chain, then switch configured path. Encrypt and restrict backups.

Release checklist: configure authentication and key rotation; rate limits; request-size limits; CORS allow-list; TLS; secure headers; secret management; least-privilege storage; reviewed model adapter; cross-user isolation tests; backup restore; monitoring; staging adversarial tests; independent review.

Limitations: search is lexical token overlap, not vector search. A hash chain detects alteration relative to the checked chain but does not authenticate writers, prove truth, or prevent privileged replacement of the database.
