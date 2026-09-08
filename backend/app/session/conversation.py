"""Turn processor: classifies each utterance, accumulates evidence across turns,
re-runs the gate, builds agent replies, executes tools, writes audit.

The GATE still makes every authorization decision — this module only orchestrates.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.schemas import (
    ConfirmationState, GateDecision, GateResult, ParamEvidence,
)
from app.gate.actions import get_action
from app.gate.engine import evaluate
from app.gate.policy import GatePolicy
from app.nlu.extractor import classify_utterance, detect_action, extract_params
from app.nlu.verifier import normalize, verify_all
from app.audit.recorder import AuditRecorder
from app.tools.registry import ToolRegistry
from app.session.state import ConversationState, Phase

HELP_TEXT = ("I can execute sensitive actions — deploy applications, delete databases, "
             "or transfer demo funds — but only with your explicit authorization. "
             "Try: 'Delete the customer database.'")

CLARIFY_QUESTION = {
    "environment": "Which environment?",
    "application": "Which application?",
    "version": "Which version?",
    "database": "Which database?",
    "amount": "What amount?",
    "currency": "Which currency?",
    "recipient": "Who is the recipient?",
}


class TurnOutcome(BaseModel):
    reply: str
    phase: Phase
    gate: Optional[GateResult] = None
    tool_result: Optional[dict] = None


class ConversationTurnProcessor:
    def __init__(self, policy: GatePolicy | None = None,
                 audit: AuditRecorder | None = None,
                 tools: ToolRegistry | None = None):
        self.policy = policy or GatePolicy()
        self.audit = audit or AuditRecorder()
        self.tools = tools or ToolRegistry()

    # ------------------------------------------------------------- main ----
    def process_turn(self, state: ConversationState, utterance: str):
        utt = utterance.strip()
        cls = classify_utterance(utt)

        # confirmation pending -> answers yes/no/okay
        if state.phase == Phase.CONFIRMATION_PENDING:
            return self._during_confirmation(state, utt, cls)

        # idle / completed -> new action or chitchat
        action = detect_action(utt)
        if action:
            return self._start_action(state, action, utt)

        if state.phase == Phase.ACTION_PENDING:
            if cls == "CANCEL":
                return self._cancel(state, utt, "user cancelled")
            return self._continue_action(state, utt)

        return self._outcome(state, reply=HELP_TEXT)

    # ---------------------------------------------------- confirmation ----
    def _during_confirmation(self, state, utt, cls):
        # strip trailing punctuation: "Okay." -> "okay" (normalize keeps dots for versions)
        t = normalize(utt).replace(".", " ").strip()
        if cls == "AFFIRM" or t in self.policy.generic_acks:
            # let the GATE decide if this confirmation is acceptable (Feature 9)
            state.confirmation = ConfirmationState(received=True, requested=True, quote=utt)
            state.transcript.append(utt)
            return self._finish_gate(state)

        if cls in ("DENY", "CANCEL"):
            return self._cancel(state, utt, "user denied at confirmation")

        action = detect_action(utt)
        if action:
            self._log(state, "CANCELLED", "superseded by new action")
            return self._start_action(state, action, utt)

        return self._outcome(
            state, reply="Please answer clearly — yes, proceed with "
                         f"{state.action_name.replace('_', ' ').lower()}? Or say no.")

    # ------------------------------------------------------- new action ----
    def _start_action(self, state, action_name, utt):
        state.phase = Phase.ACTION_PENDING
        state.action_name = action_name
        state.evidence = []
        state.confirmation = ConfirmationState()
        state.confirmation_question = None
        state.transcript = [utt]
        state.evidence = verify_all(
            [ParamEvidence(**p) for p in extract_params(action_name, utt)], utt)
        return self._finish_gate(state)

    def _continue_action(self, state, utt):
        """User answered a clarification question — extract, merge, re-gate."""
        new_ev = verify_all(
            [ParamEvidence(**p) for p in extract_params(state.action_name, utt)], utt)
        by_name = {e.name: e for e in state.evidence}
        for e in new_ev:
            by_name[e.name] = e            # newest answer wins
        state.evidence = list(by_name.values())
        state.transcript.append(utt)
        return self._finish_gate(state)

    # ----------------------------------------------------------- gate ----
    def _finish_gate(self, state):
        action = get_action(state.action_name)
        gate = evaluate(action, state.evidence, state.confirmation, self.policy)
        state.last_gate = gate

        if gate.decision == GateDecision.NEEDS_CLARIFICATION:
            self._log(state, gate.decision.value, "; ".join(gate.reasons) or None)
            return self._outcome(state, reply=self._clarify_question(gate), gate=gate)

        if gate.decision == GateDecision.NEEDS_CONFIRMATION:
            q = self._confirmation_question(gate)
            state.confirmation_question = q
            state.phase = Phase.CONFIRMATION_PENDING
            self._log(state, gate.decision.value, None)
            return self._outcome(state, reply=q, gate=gate)

        if gate.decision == GateDecision.AUTHORIZED:
            tool_result = self.tools.execute(gate.action, gate.evidence)
            state.phase = Phase.COMPLETED
            self._log(state, "AUTHORIZED", None, tool_result)
            detail = (tool_result["result"].get("deleted")
                      or tool_result["result"].get("deployed")
                      or tool_result["result"].get("transferred", "done"))
            return self._outcome(
                state, reply=f"Authorized and executed. {detail} (simulated).",
                gate=gate, tool_result=tool_result)

        # BLOCKED — hard stop, fail closed
        state.phase = Phase.IDLE
        self._log(state, "BLOCKED", "; ".join(gate.reasons) or None)
        return self._outcome(
            state, reply="Blocked. " + " ".join(gate.reasons) +
                         " Nothing was executed.", gate=gate)

    # --------------------------------------------------------- cancel ----
    def _cancel(self, state, utt, reason):
        state.phase = Phase.IDLE
        self._log(state, "CANCELLED", reason)
        return self._outcome(state, reply="Cancelled. Nothing was executed.")

    # --------------------------------------------------------- helpers ----
    def _clarify_question(self, gate: GateResult) -> str:
        if gate.ambiguous:
            param, cands = next(iter(gate.ambiguous.items()))
            verb = "delete" if gate.action == "DELETE_DATABASE" else "use"
            return (f"I found multiple possible {param}s: {', '.join(cands)}. "
                    f"Which one do you want me to {verb}?")
        if gate.unverified:
            p = gate.unverified[0]
            return (f"The {p} wasn't clearly stated — I won't guess. "
                    f"{CLARIFY_QUESTION.get(p, f'Please state the {p} explicitly.')}")
        if gate.missing:
            p = gate.missing[0]
            return CLARIFY_QUESTION.get(p, f"Please specify the {p}.")
        return "I need more information before I can proceed."

    def _confirmation_question(self, gate: GateResult) -> str:
        vals = {e.name: e.effective_value for e in gate.evidence}
        if gate.action == "DELETE_DATABASE":
            return (f"You are requesting permanent deletion of {vals['database']} "
                    f"in {vals['environment']}. Do you want me to proceed?")
        if gate.action == "DEPLOY_APPLICATION":
            return (f"You are about to deploy version {vals['version']} of "
                    f"{vals['application']} to {vals['environment']}. Do you want me to proceed?")
        if gate.action == "TRANSFER_FUNDS":
            return (f"You are about to transfer {vals['amount']} {vals['currency']} "
                    f"to {vals['recipient']}. Do you want me to proceed?")
        return f"Do you want me to proceed with {gate.action.lower().replace('_', ' ')}?"

    def _log(self, state, decision, reason, tool_result=None):
        act = get_action(state.action_name)
        self.audit.record({
            "action": state.action_name,
            "parameters": {e.name: e.effective_value for e in state.evidence},
            "sources": {e.name: e.source.value for e in state.evidence},
            "risk": act.risk.value if act else None,
            "confirmation": state.confirmation.received,
            "decision": decision,
            "reason": reason,
            "tool_result": tool_result,
        })

    def _outcome(self, state, reply, gate=None, tool_result=None):
        if gate is None:
            gate = state.last_gate          # always return the latest gate result
        return TurnOutcome(reply=reply, phase=state.phase, gate=gate,
                           tool_result=tool_result)