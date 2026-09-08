from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

from app.schemas import ConfirmationState, ParamSource
from app.gate.actions import ACTIONS
from app.gate.engine import process_request
from app.session.state import SessionManager
from app.session.conversation import ConversationTurnProcessor
from app.audit.recorder import AuditRecorder

app = FastAPI(title="Voice Action Gate", version="0.2.0")

sessions = SessionManager()
audit = AuditRecorder()
processor = ConversationTurnProcessor(audit=audit)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "voice-action-gate"}


@app.get("/api/actions")
def list_actions():
    return {name: a.model_dump() for name, a in ACTIONS.items()}


# ---------- conversational endpoint (text-first; voice plugs in later) ----------
class TurnRequest(BaseModel):
    session_id: str = "demo"
    text: str


@app.post("/api/turn")
def turn(req: TurnRequest):
    state = sessions.get_or_create(req.session_id)
    return processor.process_turn(state, req.text)


@app.get("/api/audit")
def audit_entries():
    return audit.all()


# ---------- direct gate testing (kept from v0.1) ----------
class RawParamModel(BaseModel):
    name: str
    value: Optional[str] = None
    quote: Optional[str] = None
    claimed_source: ParamSource = ParamSource.USER_EXPLICIT


class GateCheckRequestModel(BaseModel):
    action: Optional[str] = None
    transcript: str
    parameters: list[RawParamModel] = []
    confirmation_received: bool = False
    confirmation_quote: Optional[str] = None


@app.post("/api/gate/check")
def gate_check(req: GateCheckRequestModel):
    return process_request(
        action_name=req.action, transcript=req.transcript,
        raw_parameters=[p.model_dump() for p in req.parameters],
        confirmation=ConfirmationState(received=req.confirmation_received,
                                       requested=req.confirmation_received,
                                       quote=req.confirmation_quote),
    )