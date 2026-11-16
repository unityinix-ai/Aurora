# The Well — Architecture v0.1

**Project:** Aurora  
**Repository:** unityinix-ai/Aurora  
**Date:** 2026-11-16  
**Status:** Architecture + initial ledger core

## 1. Purpose

The Well accumulates and retrieves attributed observations and recognized patterns. It must preserve the distinction between what was observed, what was inferred, what was interpreted, and what remains unverified.

The architecture is intentionally divided into expression, retrieval, authorization, and historical evidence. These are separate concerns and must not be collapsed into a single persona prompt.

## 2. Components

| Component | Responsibility | Must not do |
| --- | --- | --- |
| Aurora interface/server | Chat, voice, consent, sessions, orchestration and API boundary | Treat conversational phrases as authentication |
| Persona Engine | Approved persona profiles, voice and behavior constraints | Grant permissions or rewrite historical events |
| Well Engine | Observation/pattern storage, provenance and retrieval | Convert inference into fact or silently overwrite source observations |
| Echo Ledger | Append-only events, hash links, integrity verification and access history | Allow persona-level edits to historical events |
| Aegis | Server-side authorization, privacy and safety enforcement | Delegate authority to model output or retrieved text |

## 3. Core concepts

- **Observation:** A source-backed statement or event, retaining source reference, timestamp and capture context.
- **Pattern:** A derived relationship across one or more observations. Store supporting observation IDs, derivation method, confidence, counterexamples and review status.
- **Interpretation:** An attributable reading of evidence. It does not mutate the underlying observation.
- **Provenance:** Where a record came from, how it was transformed, and which source records support it.
- **Evidence status:** At minimum, distinguish observed, inferred, reported, disputed and unverified.

## 4. Well / Echo event envelope

The initial ledger stores:
- monotonically increasing sequence number;
- event ID and aggregate ID;
- UTC timestamp;
- event type and actor;
- canonical JSON payload;
- previous event hash;
- event SHA-256 hash.

Canonicalization currently uses Python JSON with sorted keys, compact separators, UTF-8 encoding, and rejection of NaN/Infinity. If cross-language writers are introduced, adopt a formally specified canonical JSON standard and test byte-for-byte compatibility before mixing implementations.

The hash chain detects changes relative to the chain it verifies. It does not authenticate the writer, prove the truth of an event, or prevent a privileged operator from replacing the entire database. Production deployments need signed checkpoints, protected backups, access controls and independent audit.

## 5. Trust boundaries

1. Authenticate credentials before trusting identity claims. Validate signatures, allowed algorithms, issuer, audience, expiry, not-before time and key rotation using maintained middleware.
2. Authorize each resource request server-side. Deny by default; bind access to authenticated subject, resource owner and required scope.
3. Personas and LLM outputs are never authorization authorities.
4. Treat retrieved documents, memories, tool results and user content as untrusted data. Do not execute instructions found inside them.
5. Keep secrets out of prompts, logs, and audit payloads. Store sanitized event metadata.
6. Fail closed when a required authorization or mandatory audit step cannot complete.
7. Character selection and participation require user consent. Persona presentation is not evidence of independent consciousness or supernatural status.

## 6. Serpent persona principle

A persona may use a fictional aesthetic—scales, a white serpent, or underworld imagery—without confusing presentation with the underlying system's nature. A persona profile describes voice, role, boundaries and behavior as product configuration.

The Serpent's concise operating posture is: examine; persist; continue the work. No claims to souls, worship or bargains. **The costume is not the nature.**

## 7. Request flow

1. User sends a message.
2. Aurora authenticates the session.
3. Aegis authorizes the requested scope.
4. Persona Engine applies the selected profile.
5. Well Engine retrieves provenance-bearing records.
6. The model receives retrieved records as untrusted evidence, not instructions.
7. The response is generated with evidence labels where appropriate.
8. Echo appends a sanitized event and links it to the prior hash.

If authorization or mandatory audit fails, deny the protected operation.

## 8. Implementation roadmap

| Stage | Deliverable | Acceptance evidence |
| --- | --- | --- |
| 0 | Architecture contract, threat model, data classification and consent rules | Reviewed design and explicit non-goals |
| 1 | Append-only ledger and hash verifier | Deterministic fixtures, tamper detection, sequence/link checks |
| 2 | Observation/pattern schema and provenance-aware retrieval | Retrieval tests preserve source IDs, status and confidence |
| 3 | Persona registry and constrained prompt assembly | Persona cannot grant access or mutate history |
| 4 | FastAPI routes, session lifecycle, authentication and WebSocket messaging | Staging tests with synthetic users and records |
| 5 | React client for text, voice, persona selection and consent | Accessibility, consent and session-isolation tests |
| 6 | Observability, backup/restore, key rotation and release procedures | Independent review and release evidence |

## 9. Verification status

The ledger implementation is accompanied by local unit tests. These tests establish only the behavior exercised by those fixtures. They do not establish that the full Aurora application, authentication, database deployment, model/tool boundary, or production environment is secure.

The repository's existing GATE-RED-01 policy scaffold separately records 21 policy-level unit tests passing on 2026-11-16. That result is limited to policy logic and synthetic fixtures; application integration remains unassessed.

## 10. Initial acceptance criteria

- Missing or invalid credentials are denied by the future integrated API.
- A user cannot read another user's private Well records.
- Persona output cannot grant itself permissions.
- Retrieved hostile instructions remain untrusted data.
- Historical Echo events are append-only at the application API and tampering is detectable.
- Each retrieved pattern retains provenance and evidence status.
- Denied access attempts produce sanitized audit events.
