"""Tests for the Intelligence layer (front of the funnel).

The sweep reads the client strategy pillars and returns a deterministic list of
candidate seed ideas grounded in those pillars. Offline by default: no network,
no API keys, stdlib only.
"""

from engine.intelligence import intelligence


def test_returns_candidate_seeds():
    seeds = intelligence.sweep("lumen-skin")
    assert isinstance(seeds, list)
    assert len(seeds) >= 3
    for s in seeds:
        assert "idea" in s
        assert "pillar" in s
        assert "source" in s
        assert s["idea"].strip()


def test_seeds_are_grounded_in_strategy_pillars():
    seeds = intelligence.sweep("lumen-skin")
    pillars = intelligence.load_pillars("lumen-skin")
    assert pillars  # strategy.md has named pillars
    used = {s["pillar"] for s in seeds}
    # Every candidate is tagged with a real pillar from the client strategy.
    assert used.issubset(set(pillars))
    # The sweep covers more than one pillar so the strategist has range.
    assert len(used) >= 2


def test_deterministic():
    a = intelligence.sweep("lumen-skin")
    b = intelligence.sweep("lumen-skin")
    assert a == b


def test_no_network_path_without_env(monkeypatch):
    # With no DATAFORSEO/GSC/APIFY env vars, the sweep must stay offline.
    for var in ("DATAFORSEO_LOGIN", "GSC_CREDENTIALS", "APIFY_TOKEN"):
        monkeypatch.delenv(var, raising=False)
    seeds = intelligence.sweep("lumen-skin")
    assert all(s["source"].startswith("stub:") for s in seeds)
