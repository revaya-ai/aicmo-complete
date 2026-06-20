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


# ---- live vs offline path (DataForSEO injection) -----------------------------


class _FakeConfiguredClient:
    """A fake DataForSEO client that is configured and returns canned ideas.

    No network. It mimics the keyword_ideas response shape closely enough for
    the intelligence layer to turn results into seeds.
    """

    def __init__(self):
        self.calls = []

    def is_configured(self):
        return True

    def keyword_ideas(self, keywords, **kwargs):
        self.calls.append(("keyword_ideas", keywords))
        return {
            "tasks": [
                {
                    "result": [
                        {
                            "items": [
                                {"keyword": "simple skincare routine for beginners"},
                                {"keyword": "what skincare ingredients to skip"},
                                {"keyword": "3 step skincare routine results"},
                            ]
                        }
                    ]
                }
            ]
        }


class _FakeUnconfiguredClient:
    def is_configured(self):
        return False

    def keyword_ideas(self, *a, **k):  # pragma: no cover - never reached
        raise AssertionError("keyword_ideas called on an unconfigured client")


def test_offline_path_reports_stub(monkeypatch):
    for var in ("DATAFORSEO_LOGIN", "GSC_CREDENTIALS", "APIFY_TOKEN"):
        monkeypatch.delenv(var, raising=False)
    result = intelligence.sweep_with_meta("lumen-skin", dfs_client=_FakeUnconfiguredClient())
    assert result["path"] == "offline:stub"
    assert result["seeds"]
    assert all(s["source"].startswith("stub:") for s in result["seeds"])


def test_live_path_uses_injected_client():
    fake = _FakeConfiguredClient()
    result = intelligence.sweep_with_meta("lumen-skin", dfs_client=fake)
    assert result["path"] == "live:dataforseo"
    assert fake.calls, "the live path must actually query the client"
    # Live seeds carry the live source label and stay grounded in real pillars.
    assert any(s["source"] == "live:dataforseo" for s in result["seeds"])
    pillars = set(intelligence.load_pillars("lumen-skin"))
    assert {s["pillar"] for s in result["seeds"]}.issubset(pillars)


def test_live_path_falls_back_on_client_error():
    class _Boom:
        def is_configured(self):
            return True

        def keyword_ideas(self, *a, **k):
            raise RuntimeError("api down")

    result = intelligence.sweep_with_meta("lumen-skin", dfs_client=_Boom())
    # On any client error the sweep must fall back to the offline stub, not crash.
    assert result["path"] == "offline:stub"
    assert result["seeds"]


def test_sweep_still_returns_plain_list():
    # Back-compat: sweep() returns just the list, as the rest of the system expects.
    seeds = intelligence.sweep("lumen-skin", dfs_client=_FakeUnconfiguredClient())
    assert isinstance(seeds, list)
    assert seeds and "idea" in seeds[0]
