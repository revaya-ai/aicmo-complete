"""Tests for Voice of Customer, Brick Phase 0 (engine/brain/voc.py).

Phase 0 runs before Intake. It returns VoC signal (pain points and real
customer phrases) grounded in the client's 6-layer context files. The default
path is a deterministic offline stub that reads
client-data/<client>/brand-and-audience.md and strategy.md. No network call.

If a configured DataForSEO client is injected it MAY enrich the phrasing, but the
offline path must fully work on its own. These tests inject nothing, so the
offline path is exercised end to end.
"""

from engine.brain import voc


def test_offline_returns_nonempty_voc_grounded_in_context():
    signal = voc.voice_of_customer("lumen-skin", "10 step skincare routines")

    assert isinstance(signal, dict)
    assert signal["pain_points"], "expected non-empty pain points"
    assert signal["customer_phrases"], "expected non-empty customer phrases"
    # Grounded in the loaded context: the brand-and-audience file lists hype and
    # 12-step routines as turn-offs, so a pain point should reflect that.
    joined = " ".join(signal["pain_points"] + signal["customer_phrases"]).lower()
    assert "hype" in joined or "step" in joined or "ingredient" in joined


def test_offline_is_deterministic():
    a = voc.voice_of_customer("lumen-skin", "same seed")
    b = voc.voice_of_customer("lumen-skin", "same seed")
    assert a == b


def test_offline_carries_audience_and_seed():
    signal = voc.voice_of_customer("lumen-skin", "do serums actually work")
    assert signal["seed_idea"] == "do serums actually work"
    # The primary audience persona is parsed from brand-and-audience.md.
    assert "Olivia" in signal["audience"]


def test_missing_client_returns_safe_empty_shape():
    signal = voc.voice_of_customer("no-such-client", "anything")
    assert isinstance(signal["pain_points"], list)
    assert isinstance(signal["customer_phrases"], list)
    assert signal["seed_idea"] == "anything"
