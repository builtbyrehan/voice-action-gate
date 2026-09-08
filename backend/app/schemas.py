"""Core data shapes shared across the whole system."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ParamSource(str, Enum):
    """Where a parameter value came from (PRD section 13)."""
    USER_EXPLICIT = "USER_EXPLICIT"      # user literally said it  ✅
    SYSTEM_CONTEXT = "SYSTEM_CONTEXT"    # found in system data
    AI_INFERENCE = "AI_INFERENCE"        # the AI guessed it       ❌
    DEFAULT_VALUE = "DEFAULT_VALUE"      # a default was used      ❌
    UNCERTAIN = "UNCERTAIN"              # user said "probably..." ❌
    UNKNOWN = "UNKNOWN"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class GateDecision(str, Enum):
    AUTHORIZED = "AUTHORIZED"                    # run the tool
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"  # blocked, agent asks user
    NEEDS_CONFIRMATION = "NEEDS_CONFIRMATION"    # params OK, agent asks "confirm?"
    BLOCKED = "BLOCKED"                          # hard block (terminal)


class ParamEvidence(BaseModel):
    """One action parameter + proof of where its value came from."""
    name: str
    value: Optional[str] = None
    quote: Optional[str] = None                  # the user's verbatim words
    claimed_source: ParamSource = ParamSource.USER_EXPLICIT   # what the LLM claims
    source: ParamSource = ParamSource.UNKNOWN    # what we PROVED after checking
    verified: bool = False
    uncertain: bool = False
    confidence: float = 0.0
    candidates: list[str] = Field(default_factory=list)  # for ambiguous params
    resolved_value: Optional[str] = None

    @property
    def effective_value(self) -> Optional[str]:
        return self.resolved_value or self.value


class ConfirmationState(BaseModel):
    requested: bool = False
    received: bool = False
    quote: Optional[str] = None                  # what the user said to confirm


class GateCheck(BaseModel):
    check: str          # ACTION_KNOWN / MISSING_PARAMS / AMBIGUITY / EXPLICITNESS / CONFIRMATION
    passed: bool
    detail: Optional[str] = None


class GateResult(BaseModel):
    decision: GateDecision
    action: Optional[str] = None
    risk: Optional[RiskLevel] = None
    checks: list[GateCheck] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    ambiguous: dict[str, list[str]] = Field(default_factory=dict)
    unverified: list[str] = Field(default_factory=list)
    evidence: list[ParamEvidence] = Field(default_factory=list)