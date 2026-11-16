# Project Aurora — The Well

**The Well** is a provenance-aware pattern retrieval component for a multi-persona AI system.

It separates five responsibilities:

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

The initial Well core provides a SQLite-backed append-only event ledger with canonical JSON serialization, SHA-256 hash chaining, and a chain verifier.

- Implementation: [well/ledger.py](well/ledger.py)
- Tests: [tests/test_well_ledger.py](tests/test_well_ledger.py)
- Architecture: [docs/WELL_ARCHITECTURE.md](docs/WELL_ARCHITECTURE.md)
- Security boundary: [security/GATE-RED-01.md](security/GATE-RED-01.md)

Run the Well ledger tests:

```bash
python -m unittest discover -s tests -v
```

No external packages are required for the ledger core (Python standard library only).

## Status

This is an implementation starter, not a deployed production service. The Well ledger core is implemented; the FastAPI application, authentication middleware, persona runtime, vector/semantic retrieval, React client, and integrated staging security tests remain future stages. Do not infer production readiness from unit tests of isolated components.

See the architecture brief in [docs/WELL_ARCHITECTURE.md](docs/WELL_ARCHITECTURE.md).