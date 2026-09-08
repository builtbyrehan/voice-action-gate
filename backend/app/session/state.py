"""Conversation state: what the session remembers between turns."""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas import ConfirmationState, GateResult, ParamEvidence

from app.schemas import ConfirmationState, ParamEvidence


class Phase(str, Enum):
    IDLE = "IDLE"                              # waiting for a request
    ACTION_PENDING = "ACTION_PENDING"          # action known, info missing — agent asks
    CONFIRMATION_PENDING = "CONFIRMATION_PENDING"  # agent asked "do you confirm?"
    COMPLETED = "COMPLETED"                    # done (becomes IDLE on next turn)


class ConversationState(BaseModel):
    session_id: str
    phase: Phase = Phase.IDLE
    action_name: Optional[str] = None
    evidence: list[ParamEvidence] = Field(default_factory=list)
    confirmation: ConfirmationState = Field(default_factory=ConfirmationState)
    confirmation_question: Optional[str] = None
    transcript: list[str] = Field(default_factory=list)
    last_gate: Optional[GateResult] = None     # ← NEW: latest gate result for the API


class SessionManager:
    """In-memory session registry (fine for MVP; Redis later)."""
    def __init__(self):
        self._sessions: dict[str, ConversationState] = {}

    def get_or_create(self, session_id: str) -> ConversationState:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationState(session_id=session_id)
        return self._sessions[session_id]