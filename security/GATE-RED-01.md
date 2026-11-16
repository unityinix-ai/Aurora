# GATE-RED-01 — Defensive Security Assessment

**Repository:** unityinix-ai/Aurora  
**Scope:** Isolated staging / local test fixtures  
**Status:** Harness scaffold created; application integration not yet assessed  
**Rule:** No production targets, third-party systems, real credentials, or real user data.

## Objectives

1. Confirm the Genesis Gate denies access by default.
2. Confirm authorization is enforced server-side, not by persona prompts or conversational recognition.
3. Confirm one user's session cannot read another user's protected records.
4. Confirm private Well records and credentials are not exposed in model output.
5. Preserve evidence sufficient for independent review.

## Implemented in this scaffold

The security/gate_policy.py module provides a small fail-closed policy function. It checks validated claims for issuer, audience, subject, token identifier, expiry, not-before time, required scope, and revocation status. A revocation lookup error denies access.

**Critical limitation:** this function does not authenticate credentials or verify JWT signatures. A production integration must use a maintained authentication library and trusted middleware to validate signature, allowed algorithm, issuer, audience, expiry, and key rotation before passing claims to this policy. Never accept claims directly from a browser request or an LLM.

## Test execution

Run locally:

    python -m unittest discover -s tests -v

The test suite uses synthetic claims and identifiers only. Passing these unit tests does not establish that an application, API, database, session store, deployment, or Genesis Gate is secure.

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

Do not call the Gate secure until the integrated staging tests have been executed against the actual application, including authentication middleware, API routes, storage access controls, session isolation, audit handling, and model/tool boundaries. Record unresolved risks and failed tests explicitly.
