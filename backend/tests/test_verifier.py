from app.nlu.verifier import hedge_near, match_entities, normalize, phrase_in_text, verify_param
from app.nlu.catalog import DATABASES
from app.schemas import ParamEvidence, ParamSource


def test_normalize():
    assert normalize("Customer_DB, please!") == "customer db please"


def test_word_boundaries():
    assert phrase_in_text("prod", "deploy to prod") is True
    assert phrase_in_text("prod", "deploy to production") is False
    assert phrase_in_text("4.8.2", "deploy version 4.8.2 to production") is True


def test_hedge_detection():
    assert hedge_near("production", "It's probably production.") == "probably"
    assert hedge_near("production", "Deploy to production.") is None
    # hedge in another sentence must NOT taint this param
    assert hedge_near("production", "It's probably fine. Deploy to production.") is None


def test_catalog_exact_and_alias():
    assert match_entities("customer_db", DATABASES) == ["customer_db"]
    assert match_entities("delete the customer database", DATABASES) == ["customer_db"]


def test_catalog_generic_phrase_is_ambiguous():
    assert match_entities("the old database", DATABASES) == []


def test_hedge_via_value_only():
    # even without a quote, a value inside a hedged sentence is uncertain
    ev = verify_param(
        ParamEvidence(name="environment", value="production", quote=None,
                      claimed_source=ParamSource.AI_INFERENCE),
        "it's probably production",
    )
    assert ev.uncertain is True


def test_claim_without_proof_downgrades():
    ev = verify_param(
        ParamEvidence(name="environment", value="production", quote=None,
                      claimed_source=ParamSource.USER_EXPLICIT),
        "deploy the latest version",
    )
    assert ev.source == ParamSource.AI_INFERENCE
    assert ev.verified is False