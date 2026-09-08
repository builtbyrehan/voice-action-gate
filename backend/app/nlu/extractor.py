"""Rule-based extractor + utterance classifier.

This produces EXACTLY the same shape the future LLM extractor will produce
(name, value, quote, claimed_source). The verifier + gate don't care who
made the claim — they verify it the same way. Swapping in the LLM later
changes nothing downstream.

No LLM here = fully testable without API keys.
"""

from __future__ import annotations

import re

from app.nlu.catalog import CATALOG, PARAM_KIND, TYPE_KEYWORDS, Entity
from app.nlu.verifier import normalize, phrase_in_text, match_entities

VERSION_RE = re.compile(r"\b\d+(?:\.\d+)+\b")
AMOUNT_RE = re.compile(
    r"\$\s*(\d[\d,]*(?:\.\d+)?)|\b(\d[\d,]*(?:\.\d+)?)\s*(usd|dollars?|euros?|eur|inr|rupees?|rs)\b",
    re.IGNORECASE,
)
RECIPIENT_RE = re.compile(
    r"\bto\s+([a-z][a-z ]{1,30}?)(?:\s+(?:in|on|from|via|please|today|now)\b|[.!?]|$)",
    re.IGNORECASE,
)
CURRENCY_MAP = {
    "usd": "USD",
    "dollar": "USD",
    "dollars": "USD",
    "$": "USD",
    "eur": "EUR",
    "euro": "EUR",
    "euros": "EUR",
    "inr": "INR",
    "rupee": "INR",
    "rupees": "INR",
    "rs": "INR",
}

AFFIRM_RE = re.compile(
    r"\b(yes|confirm|confirmed|proceed|definitely|absolutely|do it|go ahead|delete it|do that)\b"
)
DENY_RE = re.compile(r"\b(no|nope|negative|abort|don t|do not)\b")
CANCEL_RE = re.compile(r"\b(cancel|nevermind|never mind|forget it|scratch that)\b")


# ---------------------------------------------------------------- actions ----
def detect_action(text: str) -> str | None:
    t = normalize(text)
    if ("delete" in t or "drop" in t or "remove" in t) and (
        "database" in t or "db" in t
    ):
        return "DELETE_DATABASE"
    if "deploy" in t or "release" in t:
        return "DEPLOY_APPLICATION"
    if ("transfer" in t or "send" in t or "pay" in t) and (
        "fund" in t or "money" in t or "$" in text
    ):
        return "TRANSFER_FUNDS"
    # bare "transfer 500 dollars" has no keyword pair above — catch it here
    if ("transfer" in t or "send" in t) and AMOUNT_RE.search(text):
        return "TRANSFER_FUNDS"
    return None


def classify_utterance(text: str) -> str:
    """AFFIRM / DENY / CANCEL / ACTION / INFO"""
    t = normalize(text)
    if CANCEL_RE.search(t):
        return "CANCEL"
    if DENY_RE.search(t):
        return "DENY"
    if AFFIRM_RE.search(t):
        return "AFFIRM"
    if detect_action(text):
        return "ACTION"
    return "INFO"


# ------------------------------------------------------------- parameters ----
def _find_quote(text: str, phrases: tuple[str, ...]) -> str | None:
    for p in phrases:
        m = re.search(re.escape(p), text, re.IGNORECASE)
        if m:
            return m.group(0)
    return None


def _entity_param(name: str, text: str) -> list[dict]:
    kind = PARAM_KIND[name]
    ents: list[Entity] = CATALOG[kind]
    hits = match_entities(text, ents)
    if len(hits) == 1:
        e = next(e for e in ents if e.name == hits[0])
        return [
            {
                "name": name,
                "value": hits[0],
                "quote": _find_quote(text, (e.name, *e.aliases)),
                "claimed_source": "USER_EXPLICIT",
            }
        ]
    if len(hits) > 1:
        return [
            {
                "name": name,
                "value": None,
                "candidates": hits,
                "claimed_source": "USER_EXPLICIT",
            }
        ]
    # generic mention ("the old database") -> everything is a candidate = ambiguous
    norm = normalize(text)
    for kw in TYPE_KEYWORDS[kind]:
        if phrase_in_text(kw, norm):
            m = re.search(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE)
            return [
                {
                    "name": name,
                    "value": None,
                    "quote": (
                        m.group(0) if m else kw
                    ),  # the words the user actually said
                    "candidates": [e.name for e in ents],
                    "claimed_source": "USER_EXPLICIT",
                }
            ]
    return []  # not mentioned at all


def extract_params(action_name: str, text: str) -> list[dict]:
    params: list[dict] = []
    if action_name == "DELETE_DATABASE":
        params += _entity_param("database", text)
        params += _entity_param("environment", text)

    elif action_name == "DEPLOY_APPLICATION":
        params += _entity_param("application", text)
        m = VERSION_RE.search(text)
        if m:
            params.append(
                {
                    "name": "version",
                    "value": m.group(0),
                    "quote": m.group(0),
                    "claimed_source": "USER_EXPLICIT",
                }
            )
        params += _entity_param("environment", text)

    elif action_name == "TRANSFER_FUNDS":
        m = AMOUNT_RE.search(text)
        if m:
            amount = (m.group(1) or m.group(2) or "").replace(",", "")
            params.append(
                {
                    "name": "amount",
                    "value": amount,
                    "quote": m.group(0).strip(),
                    "claimed_source": "USER_EXPLICIT",
                }
            )
            cur_raw = m.group(3) or "$"
            cur = CURRENCY_MAP.get(cur_raw.lower(), CURRENCY_MAP.get(cur_raw, cur_raw))
            params.append(
                {
                    "name": "currency",
                    "value": cur,
                    "quote": m.group(0).strip(),
                    "claimed_source": "USER_EXPLICIT",
                }
            )
        r = RECIPIENT_RE.search(text)
        if r:
            params.append(
                {
                    "name": "recipient",
                    "value": r.group(1).strip(),
                    "quote": r.group(0).strip(),
                    "claimed_source": "USER_EXPLICIT",
                }
            )
    return params
