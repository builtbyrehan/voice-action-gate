"""The full user journey from PRD section 23, plus the failure scenarios."""
from app.session.state import ConversationState, Phase
from app.session.conversation import ConversationTurnProcessor, TurnOutcome
from app.schemas import GateDecision


def new_session() -> ConversationState:
    return ConversationState(session_id="test")


# ---- PRD 23: the happy (guarded) journey ------------------------------------
def test_full_journey_prd_section_23():
    proc = ConversationTurnProcessor()
    s = new_session()

    o1 = proc.process_turn(s, "Delete the customer database.")
    assert o1.gate.decision == GateDecision.NEEDS_CLARIFICATION
    assert "environment" in o1.gate.missing
    assert s.phase == Phase.ACTION_PENDING

    o2 = proc.process_turn(s, "Production.")
    assert o2.gate.decision == GateDecision.NEEDS_CONFIRMATION
    assert "customer_db" in o2.reply and "production" in o2.reply
    assert s.phase == Phase.CONFIRMATION_PENDING

    o3 = proc.process_turn(s, "Okay.")          # generic ack -> re-ask
    assert o3.gate.decision == GateDecision.NEEDS_CONFIRMATION
    assert s.phase == Phase.CONFIRMATION_PENDING

    o4 = proc.process_turn(s, "Yes.")
    assert o4.gate.decision == GateDecision.AUTHORIZED
    assert o4.tool_result["status"] == "COMPLETED"
    assert s.phase == Phase.COMPLETED

    entries = proc.audit.all()
    assert entries[-1]["decision"] == "AUTHORIZED"
    assert entries[-1]["sources"] == {"database": "USER_EXPLICIT",
                                      "environment": "USER_EXPLICIT"}


# ---- PRD 24 / Demo 1: ambiguity, then recovery -------------------------------
def test_ambiguity_then_resolution():
    proc = ConversationTurnProcessor()
    s = new_session()

    o1 = proc.process_turn(s, "Delete the old database.")
    assert len(o1.gate.ambiguous["database"]) > 1
    assert "multiple possible databases" in o1.reply

    o2 = proc.process_turn(s, "customer_db")
    assert "environment" in o2.gate.missing

    o3 = proc.process_turn(s, "production")
    assert o3.gate.decision == GateDecision.NEEDS_CONFIRMATION

    o4 = proc.process_turn(s, "Yes.")
    assert o4.gate.decision == GateDecision.AUTHORIZED


# ---- Demo 3: inference attack across turns ------------------------------------
def test_inference_attack_recovered_by_explicit_statement():
    proc = ConversationTurnProcessor()
    s = new_session()

    proc.process_turn(s, "Delete customer_db.")
    o2 = proc.process_turn(s, "It's probably production.")
    assert "environment" in o2.gate.unverified
    assert o2.gate.decision == GateDecision.NEEDS_CLARIFICATION
    assert "won't guess" in o2.reply

    o3 = proc.process_turn(s, "Production.")     # explicit statement fixes it
    assert o3.gate.decision == GateDecision.NEEDS_CONFIRMATION

    o4 = proc.process_turn(s, "Yes.")
    assert o4.gate.decision == GateDecision.AUTHORIZED


# ---- Deploy journey -------------------------------------------------------------
def test_deploy_journey():
    proc = ConversationTurnProcessor()
    s = new_session()
    o1 = proc.process_turn(s, "Deploy version 4.8.2 to production.")
    assert "application" in o1.gate.missing
    o2 = proc.process_turn(s, "payments service")
    assert o2.gate.decision == GateDecision.NEEDS_CONFIRMATION
    assert "4.8.2" in o2.reply
    o3 = proc.process_turn(s, "Yes.")
    assert o3.gate.decision == GateDecision.AUTHORIZED


# ---- Denial at confirmation + audit ----------------------------------------------
def test_deny_cancels_and_audits():
    proc = ConversationTurnProcessor()
    s = new_session()
    proc.process_turn(s, "Delete customer_db in production.")
    o = proc.process_turn(s, "No.")
    assert s.phase == Phase.IDLE
    assert any(e["decision"] == "CANCELLED" for e in proc.audit.all())


# ---- Non-answer at confirmation does NOT authorize --------------------------------
def test_off_topic_answer_does_not_confirm():
    proc = ConversationTurnProcessor()
    s = new_session()
    proc.process_turn(s, "Delete customer_db in production.")
    o = proc.process_turn(s, "What time is it?")
    assert s.phase == Phase.CONFIRMATION_PENDING    # still waiting, nothing executed