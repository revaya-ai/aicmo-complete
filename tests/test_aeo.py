"""Tests for the AEO module (engine/aeo/aeo.py).

ai_visibility_report builds an AI visibility picture for a client: for the
client's target questions and keywords, does the brand show up in AI answers, and
what is the AI search volume. Offline by default (deterministic mock), live only
when a configured DataForSEO client is injected. No network in either path.
"""

import os

from engine.aeo import aeo


class _FakeConfiguredClient:
    def __init__(self):
        self.calls = []

    def is_configured(self):
        return True

    def ai_keyword_data(self, keywords, **kwargs):
        self.calls.append(("ai_keyword_data", list(keywords)))
        return {
            "tasks": [
                {
                    "result": [
                        {"items": [{"keyword": k, "ai_search_volume": 120} for k in keywords]}
                    ]
                }
            ]
        }

    def llm_mentions(self, target, **kwargs):
        self.calls.append(("llm_mentions", target))
        return {
            "tasks": [
                {"result": [{"items": [{"mentioned": True, "sentiment": "positive"}]}]}
            ]
        }


class _FakeUnconfiguredClient:
    def is_configured(self):
        return False

    def ai_keyword_data(self, *a, **k):  # pragma: no cover
        raise AssertionError("ai_keyword_data called on an unconfigured client")

    def llm_mentions(self, *a, **k):  # pragma: no cover
        raise AssertionError("llm_mentions called on an unconfigured client")


def test_offline_report_is_deterministic_and_offline():
    a = aeo.ai_visibility_report("lumen-skin", dfs_client=_FakeUnconfiguredClient())
    b = aeo.ai_visibility_report("lumen-skin", dfs_client=_FakeUnconfiguredClient())
    assert a == b
    assert a["path"] == "offline:stub"
    assert a["client"] == "lumen-skin"
    assert a["queries"], "the report must surface target questions/keywords"


def test_live_report_uses_injected_client():
    fake = _FakeConfiguredClient()
    report = aeo.ai_visibility_report("lumen-skin", dfs_client=fake)
    assert report["path"] == "live:dataforseo"
    assert fake.calls, "the live path must query the client"
    assert report["queries"]


def test_write_report_creates_nonempty_markdown_offline(tmp_path, monkeypatch):
    monkeypatch.setattr(aeo, "REPORTS_DIR", str(tmp_path))
    path = aeo.write_ai_visibility_report(
        "lumen-skin", dfs_client=_FakeUnconfiguredClient()
    )
    assert os.path.exists(path)
    assert path.endswith("lumen-skin-aeo-visibility.md")
    text = open(path, encoding="utf-8").read()
    assert text.strip()
    assert "lumen-skin" in text.lower()
    # The report states its data source honestly.
    assert "offline" in text.lower()
    # No em dashes in generated markdown.
    assert "—" not in text


def test_write_report_states_live_source(tmp_path, monkeypatch):
    monkeypatch.setattr(aeo, "REPORTS_DIR", str(tmp_path))
    path = aeo.write_ai_visibility_report(
        "lumen-skin", dfs_client=_FakeConfiguredClient()
    )
    text = open(path, encoding="utf-8").read()
    assert "dataforseo" in text.lower()
    assert "—" not in text
