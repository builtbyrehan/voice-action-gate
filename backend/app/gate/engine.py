"""THE ACTION GATE — deterministic policy engine. No LLM. No network. Pure code.

Checks, in order (PRD section 28):
  1. ACTION_KNOWN      2. MISSING_PARAMS      3. AMBIGUITY
  4. EXPLICITNESS      5. CONFIRMATION

Fail-closed: any doubt => not authorized.
"""
from __future__ import annotations

from typing import Optional

from app.schemas import (
    ConfirmationState,
    GateCheck,
    GateDecision,
    GateResult,
    ParamEvidence,
    ParamSource,
    RiskLevel,
)
from app.gate.actions import ActionDefinition, get_action
from app.gate.policy import GatePolicy
from app.nlu.verifier import normalize, verify_all

def _is_generic_ack(quote: str, policy: GatePolicy) -> bool:
    # normalize() keeps dots (needed for versions like 4.8.2), but spoken
    # confirmations end with punctuation ("Okay.") — drop dots before comparing.
    q = normalize(quote).replace(".", " ").strip()
    return q in policy.generic_acks


def evaluate(
    action: Optional[ActionDefinition],
    evidence: list[ParamEvidence],
    confirmation: ConfirmationState,
    policy: GatePolicy,
) -> GateResult:
    checks: list[GateCheck] = []
    reasons: list[str] = []
    missing: list[str] = []
    ambiguous: dict[str, list[str]] = {}
    unverified: list[str] = []

    # ---- 1. ACTION_KNOWN -------------------------------------------------
    if action is None:
        checks.append(GateCheck(check="ACTION_KNOWN", passed=False,
                                detail="Unknown or unsupported action"))
        return GateResult(
            decision=GateDecision.BLOCKED, action=None, risk=None,
            checks=checks, reasons=["Unknown action — nothing to authorize"],
            evidence=evidence,
        )

    checks.append(GateCheck(check="ACTION_KNOWN", passed=True))
    emap = {ev.name: ev for ev in evidence}

    # ---- 2. MISSING_PARAMS -----------------------------------------------
    for p in action.required_params:
        ev = emap.get(p)
        if ev is None or ev.effective_value is None:
            if not (ev and ev.candidates):        # ambiguous params are reported separately
                missing.append(p)
    checks.append(GateCheck(check="MISSING_PARAMS", passed=not missing,
                            detail=", ".join(missing) if missing else None))

    # ---- 3. AMBIGUITY ------------------------------------------------------
    for p in action.required_params:
        ev = emap.get(p)
        if ev and len(ev.candidates) > 1:
            ambiguous[p] = ev.candidates
    checks.append(GateCheck(check="AMBIGUITY", passed=not ambiguous,
                            detail=("; ".join(f"{p}: {', '.join(c)}" for p, c in ambiguous.items())
                                    or None)))

    # ---- 4. EXPLICITNESS (strict only for HIGH risk, PRD section 13) --------
    if action.risk == RiskLevel.HIGH:
        for p in action.required_params:
            if p in missing or p in ambiguous:
                continue
            ev = emap.get(p)
            if ev is None:
                continue
            if ev.source != ParamSource.USER_EXPLICIT or ev.uncertain:
                unverified.append(p)              # inferred / uncertain / downgraded
    checks.append(GateCheck(check="EXPLICITNESS", passed=not unverified,
                            detail=", ".join(unverified) if unverified else None))

    # ---- 5. CONFIRMATION ----------------------------------------------------
    confirm_ok = True
    confirm_detail: Optional[str] = None
    if action.requires_confirmation:
        if not confirmation.received:
            confirm_ok, confirm_detail = False, "No confirmation yet"
        elif not confirmation.quote:
            confirm_ok, confirm_detail = False, "Confirmation quote missing"
        elif policy.strict_confirmation and _is_generic_ack(confirmation.quote, policy):
            confirm_ok = False
            confirm_detail = "Generic acknowledgement is not sufficient for HIGH risk"
    checks.append(GateCheck(check="CONFIRMATION", passed=confirm_ok, detail=confirm_detail))

    # ---- human-readable reasons (explainability, PRD section 31) ------------
    reasons += [f"Missing explicit {p}" for p in missing]
    reasons += [f"Ambiguous {p}: {', '.join(c)}" for p, c in ambiguous.items()]
    reasons += [f"{p} was inferred or uncertain — not explicitly stated by the user"
                for p in unverified]
    if not confirm_ok and confirm_detail:
        reasons.append(confirm_detail)

    # ---- decision ------------------------------------------------------------
    if missing or ambiguous or unverified:
        decision = GateDecision.NEEDS_CLARIFICATION   # blocked, but agent can ask
    elif not confirm_ok:
        decision = GateDecision.NEEDS_CONFIRMATION
    elif all(c.passed for c in checks):
        decision = GateDecision.AUTHORIZED
    else:
        decision = GateDecision.BLOCKED               # safety net: fail closed

    return GateResult(
        decision=decision, action=action.name, risk=action.risk,
        checks=checks, reasons=reasons,
        missing=missing, ambiguous=ambiguous, unverified=unverified,
        evidence=evidence,
    )


def process_request(
    action_name: str | None,
    transcript: str,
    raw_parameters: list[dict],
    confirmation: ConfirmationState | None = None,
    policy: GatePolicy | None = None,
) -> GateResult:
    """Full deterministic pipeline: build evidence -> verify provenance -> gate.

    raw_parameters: the shape the future LLM extractor will produce, e.g.
        {"name": "database", "value": "customer_db",
         "quote": "the customer database", "claimed_source": "USER_EXPLICIT"}
    """
    policy = policy or GatePolicy()
    confirmation = confirmation or ConfirmationState()
    action = get_action(action_name)
    evidence = verify_all([ParamEvidence(**raw) for raw in raw_parameters], transcript)
    return evaluate(action, evidence, confirmation, policy)