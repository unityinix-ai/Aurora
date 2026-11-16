from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from api.model_adapter import OpenAICompatibleAdapter
from security.jwt_auth import JWTVerifier
from well.ledger import WellLedger
from well.records import WellService
from personas.registry import get_persona, list_personas, render_persona_context

app = FastAPI(title="Aurora / The Well API", version="0.2.0")
bearer = HTTPBearer(auto_error=False)
app.state.ledger = WellLedger(os.getenv("WELL_DB", "well.sqlite3"))
app.state.well = WellService(app.state.ledger)


def _csv_env(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_csv_env("CORS_ORIGINS", ""),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=_csv_env("ALLOWED_HOSTS", "localhost,127.0.0.1"),
)

# Partial/malformed configuration aborts startup; completely absent configuration
# leaves protected routes closed with 401/503 rather than accepting synthetic claims.
app.state.authenticator = JWTVerifier.from_env()
app.state.model_adapter = OpenAICompatibleAdapter.from_env()


class ObservationIn(BaseModel):
    source_ref: str = Field(min_length=1, max_length=500)
    text: str = Field(min_length=1, max_length=10000)
    evidence_status: str = "reported"


class PatternIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    summary: str = Field(min_length=1, max_length=5000)
    supporting_event_ids: list[str] = Field(min_length=1, max_length=100)
    derivation: str = Field(min_length=1, max_length=2000)
    confidence: float = Field(ge=0, le=1)
    counterexamples: list[str] = Field(default_factory=list, max_length=100)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    persona: str = "neutral"
    consent: bool = False


async def claims_from_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    verifier = app.state.authenticator
    if credentials is None or verifier is None:
        raise HTTPException(401, "Authentication is not configured")
    try:
        claims = verifier(credentials.credentials)
        if hasattr(claims, "__await__"):
            claims = await claims
    except Exception:
        raise HTTPException(401, "Invalid credential")
    if not isinstance(claims, dict) or not isinstance(claims.get("sub"), str) or not claims["sub"].strip():
        raise HTTPException(401, "Invalid authenticated subject")
    return claims


def require_scope(claims: dict, scope: str) -> None:
    scopes = claims.get("scope", [])
    if isinstance(scopes, str):
        scopes = scopes.split()
    if not isinstance(scopes, (list, tuple, set)) or scope not in scopes:
        raise HTTPException(403, "Insufficient scope")


@app.get("/health")
def health():
    verification = app.state.ledger.verify()
    return {
        "status": "ok" if verification["valid"] else "degraded",
        "authentication_configured": callable(app.state.authenticator),
        "model_adapter_configured": callable(app.state.model_adapter),
        "ledger": verification,
    }


@app.get("/personas")
def personas():
    return [{"key": p.key, "display_name": p.display_name, "role": p.role} for p in list_personas()]


@app.post("/observations", status_code=201)
def add_observation(body: ObservationIn, claims: dict = Depends(claims_from_token)):
    require_scope(claims, "well:write")
    try:
        return app.state.well.add_observation(
            owner_id=claims["sub"], actor=claims["sub"], **body.model_dump()
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@app.post("/patterns", status_code=201)
def add_pattern(body: PatternIn, claims: dict = Depends(claims_from_token)):
    require_scope(claims, "well:write")
    try:
        return app.state.well.propose_pattern(
            owner_id=claims["sub"], actor=claims["sub"], **body.model_dump()
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@app.get("/search")
def search(q: str = Query(min_length=1, max_length=500), limit: int = 20,
           claims: dict = Depends(claims_from_token)):
    require_scope(claims, "well:read")
    return app.state.well.search(owner_id=claims["sub"], query=q, limit=max(1, min(limit, 100)))


@app.get("/records/{event_id}")
def record(event_id: str, claims: dict = Depends(claims_from_token)):
    require_scope(claims, "well:read")
    result = app.state.well.get_record(claims["sub"], event_id)
    if result is None:
        raise HTTPException(404, "Record not found")
    return result


@app.post("/chat")
async def chat(body: ChatIn, claims: dict = Depends(claims_from_token)):
    require_scope(claims, "well:chat")
    if not body.consent:
        raise HTTPException(400, "Explicit consent required")
    try:
        persona = get_persona(body.persona)
    except ValueError:
        raise HTTPException(422, "Persona is not approved")
    adapter = app.state.model_adapter
    if adapter is None:
        raise HTTPException(503, "No model adapter configured")
    context = {
        "persona_context": render_persona_context(persona),
        "user_id": claims["sub"],
        "message": body.message,
        "retrieved_evidence": app.state.well.search(
            owner_id=claims["sub"], query=body.message, limit=8
        ),
    }
    try:
        response = adapter(context)
        if hasattr(response, "__await__"):
            response = await response
    except Exception:
        raise HTTPException(502, "Model provider request failed")
    return {"persona": persona.key, "response": response}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    auth_header = websocket.headers.get("authorization", "")
    verifier = app.state.authenticator
    if not auth_header.startswith("Bearer ") or verifier is None:
        await websocket.close(code=4401)
        return
    try:
        claims = verifier(auth_header[7:])
        if hasattr(claims, "__await__"):
            claims = await claims
        if not isinstance(claims, dict) or not isinstance(claims.get("sub"), str):
            raise ValueError("invalid subject")
        require_scope(claims, "well:read")
    except Exception:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    try:
        await websocket.send_json({"type": "connected"})
        while True:
            message = await websocket.receive_text()
            await websocket.send_json({
                "type": "ack",
                "received_chars": len(message),
                "note": "Transport only; no model response generated.",
            })
    except WebSocketDisconnect:
        return
