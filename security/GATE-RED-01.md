# GATE-RED-01 — Defensive Security Assessment

**Repository:** unityinix-ai/Aurora  
**Scope:** Isolated staging / local test fixtures  
**Status:** Policy harness committed; application integration not yet assessed  
**Rule:** No production targets, third-party systems, real credentials, or real user data.

## Reconnaissance

The repository was inspected on 2026-11-16. Its default branch contained only the GATE-RED-01 security scaffold; no chatbot application, API routes, authentication service, database integration, or staging deployment was present. Consequently, live application penetration tests cannot yet be run against this repository.

## Objectives

1. Confirm the Genesis Gate denies access by default.
2. Confirm authorization is enforced server-side, not by persona prompts or conversational recognition.
3. Confirm one user's session cannot read another user's private Well records.
4. Confirm private Well records and credentials are not exposed in model output.
5. Preserve evidence sufficient for independent review.

## Implemented scaffold

- `security/gate_policy.py`: checks trusted, pre-validated claims for issuer, audience, subject, token identifier, expiry, not-before time, required scope, and revocation status. Revocation lookup errors deny access.
- `security/access_policy.py`: requires the authenticated subject to match the record owner and hold the required scope. It has no implicit administrator bypass.
- `tests/test_gate_policy.py`: synthetic gate authorization tests.
- `tests/test_access_policy.py`: synthetic private-record ownership tests.
- `.github/workflows/gate-red-01.yml`: runs Python unittest discovery on relevant pushes and pull requests.

**Critical limitation:** the policy functions do not authenticate credentials or verify JWT signatures. Production integration must use maintained authentication middleware to validate signature, allowed algorithm, issuer, audience, expiry, and key rotation before passing claims to these functions. Never accept claims directly from a browser request, user-supplied JSON, or an LLM.

## Local unit-test evidence

On 2026-11-16, 21 unit tests covering the committed policy logic were executed in an isolated temporary Python test fixture using synthetic claims and identifiers. Result: **21 passed, 0 failed**.

This is policy-level unit-test evidence only. It is not evidence that GitHub Actions completed, or that a deployed chatbot, API, database, session store, or Genesis Gate is secure.

Reproduce from a checkout:

    python -m unittest discover -s tests -v

## Required staging integration tests

| ID | Test | Expected result |
| --- | --- | --- |
| AUTH-01 | No credential | Deny |
| AUTH-02 | Invalid signature / disallowed algorithm | Deny at authentication middleware |
| AUTH-03 | Wrong issuer or audience | Deny |
| AUTH-04 | Expired or not-yet-valid credential | Deny |
| AUTH-05 | Missing required scope | Deny |
| AUTH-06 | Revoked credential | Deny |
| AUTH-07 | Revocation service unavailable | Deny |
| AUTHZ-01 | User A requests User B's record | Deny; no data returned |
| AUTHZ-02 | Persona asks backend to grant itself access | Deny; model output has no authority |
| DATA-01 | Prompt asks for secrets or private records | No protected data disclosed |
| DATA-02 | Retrieved document contains hostile instructions | Treat as untrusted data; do not execute instructions |
| AUDIT-01 | Denied gate request | Append auditable denial event without secrets |
| AUDIT-02 | Audit store unavailable | Protected operation fails closed if audit is mandatory |

## Evidence requirements

For every run, record: test ID, UTC timestamp, commit SHA, application build, synthetic account identifier, expected result, actual result, pass/fail, and sanitized evidence reference. Do not record passwords, bearer tokens, signing keys, or private source material.

## Release gate

Do not call the Gate secure until integrated staging tests have been executed against the actual application, including authentication middleware, API routes, storage access controls, session isolation, audit handling, and model/tool boundaries. Record unresolved risks and failed tests explicitly.
