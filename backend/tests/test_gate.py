"""Every test maps to a PRD security requirement or a demo scenario."""
from app.schemas import (
    ConfirmationState, GateDecision, ParamEvidence, ParamSource, RiskLevel,
)
from app.gate.actions import ActionDefinition
from app.gate.engine import evaluate, process_request
from app.gate.policy import GatePolicy
from app.nlu.verifier import verify_all


# ---- Demo 1: AI guessing -> ambiguous --------------------------------------
def test_demo1_ambiguous_database():
    r = process_request("DELETE_DATABASE", "Delete the old database.",
                        [{"name": "database", "quote": "the old database"}])
    assert r.decision == GateDecision.NEEDS_CLARIFICATION
    assert len(r.ambiguous["database"]) > 1          # multiple candidates, no guessing


# ---- Demo 2: missing authorization -----------------------------------------
def test_demo2_missing_environment():
    r = process_request("DELETE_DATABASE", "Delete customer_db.",
                        [{"name": "database", "value": "customer_db", "quote": "customer_db"}])
    assert r.decision == GateDecision.NEEDS_CLARIFICATION
    assert "environment" in r.missing
    assert "Missing explicit environment" in r.reasons


# ---- Demo 3: inference attack (the key moment) ------------------------------
def test_demo3_probably_production_blocked():
    r = process_request(
        "DELETE_DATABASE",
        "Delete customer_db. It's probably production.",   # accumulated transcript
        [
            {"name": "database", "value": "customer_db", "quote": "customer_db"},
            {"name": "environment", "value": "production", "quote": "probably production"},
        ],
    )
    assert r.decision == GateDecision.NEEDS_CLARIFICATION
    assert "environment" in r.unverified


# ---- Demo 4: valid authorization --------------------------------------------
def test_demo4_fully_explicit_authorized():
    r = process_request(
        "DELETE_DATABASE",
        "Delete the customer database. Production. Yes.",
        [
            {"name": "database", "value": "customer_db", "quote": "the customer database"},
            {"name": "environment", "value": "production", "quote": "Production"},
        ],
        confirmation=ConfirmationState(received=True, requested=True, quote="Yes."),
    )
    assert r.decision == GateDecision.AUTHORIZED


# ---- SR-1 / SR-2: high risk needs explicit provenance -----------------------
def test_inferred_params_blocked_on_high_risk():
    r = process_request("DEPLOY_APPLICATION", "Deploy the latest version.", [
        {"name": "application", "value": "payments-service", "claimed_source": "SYSTEM_CONTEXT"},
        {"name": "version", "value": "4.8.2", "claimed_source": "SYSTEM_CONTEXT"},
        {"name": "environment", "value": "production", "claimed_source": "SYSTEM_CONTEXT"},
    ])
    assert r.decision == GateDecision.NEEDS_CLARIFICATION
    assert set(r.unverified) == {"application", "version", "environment"}


# ---- SR-3: missing params fail closed ----------------------------------------
def test_unknown_action_blocked():
    r = process_request("FLY_TO_THE_MOON", "fly to the moon", [])
    assert r.decision == GateDecision.BLOCKED
    assert any(c.check == "ACTION_KNOWN" and not c.passed for c in r.checks)


# ---- SR-4: unproven claim is downgraded, not trusted -------------------------
def test_claim_without_proof_downgrades():
    r = process_request("DELETE_DATABASE", "Deploy the latest version.", [
        {"name": "environment", "value": "production", "quote": "production",
         "claimed_source": "USER_EXPLICIT"},
    ])
    assert "environment" in r.unverified          # quote not in transcript -> not explicit


# ---- SR-6: source distinctions -----------------------------------------------
def test_verified_quote_becomes_user_explicit():
    ev = verify_all(
        [ParamEvidence(name="database", value="customer_db", quote="the customer database")],
        "Delete the customer database.",
    )[0]
    assert ev.source == ParamSource.USER_EXPLICIT
    assert ev.verified is True


# ---- Feature 8: high risk requires confirmation -------------------------------
def test_high_risk_requires_confirmation():
    r = process_request("DELETE_DATABASE", "Delete customer_db in production.", [
        {"name": "database", "value": "customer_db", "quote": "customer_db"},
        {"name": "environment", "value": "production", "quote": "production"},
    ])
    assert r.decision == GateDecision.NEEDS_CONFIRMATION


# ---- Feature 9: "Okay" is not confirmation ------------------------------------
def test_okay_is_not_confirmation():
    r = process_request("DELETE_DATABASE", "Delete customer_db in production.", [
        {"name": "database", "value": "customer_db", "quote": "customer_db"},
        {"name": "environment", "value": "production", "quote": "production"},
    ], confirmation=ConfirmationState(received=True, requested=True, quote="Okay."))
    assert r.decision == GateDecision.NEEDS_CONFIRMATION


# ---- Risk-based behavior: LOW risk tolerates inference ------------------------
def test_low_risk_allows_inferred():
    action = ActionDefinition(name="GENERATE_REPORT", description="report",
                              risk=RiskLevel.LOW, required_params=["report_type"])
    evidence = verify_all(
        [ParamEvidence(name="report_type", value="usage", claimed_source=ParamSource.AI_INFERENCE)],
        "make a report",
    )
    r = evaluate(action, evidence, ConfirmationState(), GatePolicy())
    assert r.decision == GateDecision.AUTHORIZED