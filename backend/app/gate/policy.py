"""Security policy knobs (PRD Feature 9: confirmation must be specific)."""
from dataclasses import dataclass

# whole-utterance acknowledgements that are NOT specific enough for HIGH risk
GENERIC_ACKS = frozenset({"ok", "okay", "fine", "alright", "yeah", "yep", "yup", "sure"})


@dataclass
class GatePolicy:
    strict_confirmation: bool = True          # HIGH risk needs specific confirmation
    generic_acks: frozenset = GENERIC_ACKS