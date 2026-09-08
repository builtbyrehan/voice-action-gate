"""Deterministic provenance verification. NO LLM here — this is the trust boundary.

The LLM extractor PROPOSES parameters with a claimed source and a quote.
This module PROVES (or refutes) that claim against the raw transcript.

Fail-closed rule: a claim we cannot prove is downgraded to AI_INFERENCE.
"""
from __future__ import annotations

import re
from typing import Optional

from app.schemas import ParamEvidence, ParamSource
from app.nlu.catalog import CATALOG, PARAM_KIND, TYPE_KEYWORDS, Entity

# words that signal the user is guessing, not authorizing
HEDGES = (
    "probably", "maybe", "perhaps", "possibly", "presumably",
    "i think", "i guess", "i believe", "not sure",
    "might be", "could be",
    "assume", "assuming", "let's say", "lets say",
)


def normalize(text: str) -> str:
    """Lowercase, underscores->spaces, drop punctuation (keep dots for versions)."""
    t = text.lower().replace("_", " ")
    t = re.sub(r"[^a-z0-9\s.]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def phrase_in_text(phrase: str, text: str) -> bool:
    """Word-boundary aware containment on normalized text.
    'prod' does NOT match inside 'production'. 'customer db' DOES match 'customer_db'."""
    p = re.escape(normalize(phrase))
    if not p:
        return False
    pattern = rf"(?<![a-z0-9]){p}(?![a-z0-9])"
    return re.search(pattern, normalize(text)) is not None


def sentences(text: str) -> list[str]:
    parts = re.split(r"[.!?]+", text)
    return [p.strip() for p in parts if p.strip()]


def hedge_near(quote: str, transcript: str) -> Optional[str]:
    """Return the hedge word if one appears in the same sentence as the quote."""
    sents = sentences(transcript)
    if len(sents) <= 1:
        scope = [transcript]                      # spoken text often has no punctuation
    else:
        q = normalize(quote)
        scope = [s for s in sents if q and (q in normalize(s) or normalize(s) in q)]
    for s in scope:
        for h in HEDGES:
            if phrase_in_text(h, s):
                return h
    return None


def match_entities(text: str, entities: list[Entity]) -> list[str]:
    """All catalog entities whose name/alias appears in the text."""
    if not text:
        return []
    hits: list[str] = []
    for e in entities:
        phrases = (e.name, *e.aliases)
        if any(phrase_in_text(p, text) for p in phrases):
            hits.append(e.name)
    return hits


def _type_keyword_candidates(text: str, kind: str) -> list[str]:
    """'the old database' -> every database is a candidate (ambiguous, do not guess)."""
    norm = normalize(text)
    for kw in TYPE_KEYWORDS.get(kind, ()):
        if phrase_in_text(kw, norm):
            return [e.name for e in CATALOG[kind]]
    return []


def verify_param(ev: ParamEvidence, transcript: str) -> ParamEvidence:
    """Prove or refute one parameter's provenance. Mutates and returns ev."""
    # 1. prove (or refute) explicit provenance against the transcript
    in_quote = bool(ev.quote) and phrase_in_text(ev.quote, transcript)
    in_value = bool(ev.value) and phrase_in_text(ev.value, transcript)

    if in_quote or in_value:
        ev.verified = True
        ev.source = ParamSource.USER_EXPLICIT
        ev.confidence = 0.99
    elif ev.claimed_source == ParamSource.USER_EXPLICIT:
        ev.verified = False                      # claimed but unprovable -> downgrade
        ev.source = ParamSource.AI_INFERENCE
    else:
        ev.source = ev.claimed_source

    # 2. hedge words near the value -> uncertain ("It's probably production")
    probe = ev.quote or ev.value
    if probe and hedge_near(probe, transcript):
        ev.uncertain = True

    # 3. resolve against the entity catalog (ambiguity detection)
    kind = PARAM_KIND.get(ev.name)
    if kind:
        text = ev.value or ev.quote or ""
        hits = match_entities(text, CATALOG[kind])
        if len(hits) == 1:
            ev.resolved_value = hits[0]
            ev.candidates = []
        elif len(hits) > 1:
            ev.candidates = hits
        elif not ev.candidates:
            # don't wipe candidates supplied by the extractor (generic mentions)
            ev.candidates = _type_keyword_candidates(text, kind)
    return ev


def verify_all(evidence: list[ParamEvidence], transcript: str) -> list[ParamEvidence]:
    return [verify_param(ev, transcript) for ev in evidence]