"""Tests for the DataForSEO client (engine/integrations/dataforseo.py).

The client is stdlib only (urllib + base64). It never makes a real network call.
These tests monkeypatch urllib.request.urlopen so no socket is ever opened, and
assert the request the client would have sent: the endpoint, the Basic auth
header built from the env credentials, and that the body is a JSON array of task
objects (the DataForSEO convention).

When the env vars are unset the client is not configured: is_configured() is
False and every method raises DataForSEONotConfigured before touching the
network.
"""

import base64
import json

import pytest

from engine.integrations import dataforseo


class _FakeResponse:
    """Minimal stand-in for the object urllib.request.urlopen returns."""

    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _capture_urlopen(captured: dict, payload: dict):
    """Build a fake urlopen that records the Request it was handed."""

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        captured["body"] = req.data
        captured["method"] = req.get_method()
        return _FakeResponse(payload)

    return fake_urlopen


def _configure(monkeypatch, login="user@example.com", password="secret-pass"):
    monkeypatch.setenv("DATAFORSEO_LOGIN", login)
    monkeypatch.setenv("DATAFORSEO_PASSWORD", password)


# ---- is_configured -----------------------------------------------------------


def test_not_configured_when_env_unset(monkeypatch):
    monkeypatch.delenv("DATAFORSEO_LOGIN", raising=False)
    monkeypatch.delenv("DATAFORSEO_PASSWORD", raising=False)
    client = dataforseo.DataForSEOClient()
    assert client.is_configured() is False


def test_not_configured_when_only_one_var_set(monkeypatch):
    monkeypatch.setenv("DATAFORSEO_LOGIN", "user@example.com")
    monkeypatch.delenv("DATAFORSEO_PASSWORD", raising=False)
    assert dataforseo.DataForSEOClient().is_configured() is False


def test_not_configured_when_var_empty(monkeypatch):
    monkeypatch.setenv("DATAFORSEO_LOGIN", "user@example.com")
    monkeypatch.setenv("DATAFORSEO_PASSWORD", "")
    assert dataforseo.DataForSEOClient().is_configured() is False


def test_configured_when_both_set(monkeypatch):
    _configure(monkeypatch)
    assert dataforseo.DataForSEOClient().is_configured() is True


# ---- methods raise when not configured (no network) --------------------------


def test_methods_raise_when_not_configured(monkeypatch):
    monkeypatch.delenv("DATAFORSEO_LOGIN", raising=False)
    monkeypatch.delenv("DATAFORSEO_PASSWORD", raising=False)
    # If any method tried the network, this would blow up loudly instead.
    monkeypatch.setattr(
        dataforseo.urllib.request,
        "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network was called")),
    )
    client = dataforseo.DataForSEOClient()
    with pytest.raises(dataforseo.DataForSEONotConfigured):
        client.serp_organic_live("simple skincare routine")
    with pytest.raises(dataforseo.DataForSEONotConfigured):
        client.keyword_ideas(["skincare routine"])
    with pytest.raises(dataforseo.DataForSEONotConfigured):
        client.related_keywords("skincare routine")
    with pytest.raises(dataforseo.DataForSEONotConfigured):
        client.search_volume(["skincare routine"])
    with pytest.raises(dataforseo.DataForSEONotConfigured):
        client.ai_keyword_data(["skincare routine"])
    with pytest.raises(dataforseo.DataForSEONotConfigured):
        client.llm_responses("what is a simple skincare routine")
    with pytest.raises(dataforseo.DataForSEONotConfigured):
        client.llm_mentions("Lumen Skin")
    with pytest.raises(dataforseo.DataForSEONotConfigured):
        client.ranked_keywords("lumenskin.com")
    with pytest.raises(dataforseo.DataForSEONotConfigured):
        client.serp_competitors(["skincare routine"])
    with pytest.raises(dataforseo.DataForSEONotConfigured):
        client.llm_scraper("what is a simple routine")


# ---- auth header + request shape ---------------------------------------------


def test_basic_auth_header_built_from_env(monkeypatch):
    _configure(monkeypatch, "alice@brand.io", "topsecret")
    captured = {}
    monkeypatch.setattr(
        dataforseo.urllib.request, "urlopen", _capture_urlopen(captured, {"tasks": []})
    )
    client = dataforseo.DataForSEOClient()
    client.keyword_ideas(["skincare routine"])

    expected = base64.b64encode(b"alice@brand.io:topsecret").decode("ascii")
    headers = {k.lower(): v for k, v in captured["headers"].items()}
    assert headers["authorization"] == f"Basic {expected}"
    assert "application/json" in headers["content-type"]


def test_payload_is_json_array(monkeypatch):
    _configure(monkeypatch)
    captured = {}
    monkeypatch.setattr(
        dataforseo.urllib.request, "urlopen", _capture_urlopen(captured, {"tasks": []})
    )
    client = dataforseo.DataForSEOClient()
    client.keyword_ideas(["skincare routine"], location_name="United States")

    body = json.loads(captured["body"].decode("utf-8"))
    assert isinstance(body, list)
    assert len(body) == 1
    assert isinstance(body[0], dict)
    assert captured["method"] == "POST"


# ---- endpoints ---------------------------------------------------------------


def _run(monkeypatch, call):
    _configure(monkeypatch)
    captured = {}
    monkeypatch.setattr(
        dataforseo.urllib.request, "urlopen", _capture_urlopen(captured, {"tasks": []})
    )
    call(dataforseo.DataForSEOClient())
    return captured


def test_serp_organic_endpoint(monkeypatch):
    cap = _run(monkeypatch, lambda c: c.serp_organic_live("simple skincare routine"))
    assert cap["url"].endswith("/serp/google/organic/live/advanced")
    assert cap["url"].startswith("https://api.dataforseo.com/v3/")


def test_keyword_ideas_endpoint(monkeypatch):
    cap = _run(monkeypatch, lambda c: c.keyword_ideas(["skincare routine"]))
    assert cap["url"].endswith("/dataforseo_labs/google/keyword_ideas/live")


def test_related_keywords_endpoint(monkeypatch):
    cap = _run(monkeypatch, lambda c: c.related_keywords("skincare routine"))
    assert cap["url"].endswith("/dataforseo_labs/google/related_keywords/live")


def test_search_volume_endpoint(monkeypatch):
    cap = _run(monkeypatch, lambda c: c.search_volume(["skincare routine"]))
    assert cap["url"].endswith("/keywords_data/google_ads/search_volume/live")


def test_ai_keyword_data_endpoint(monkeypatch):
    cap = _run(monkeypatch, lambda c: c.ai_keyword_data(["skincare routine"]))
    assert cap["url"].endswith(
        "/ai_optimization/ai_keyword_data/keywords_search_volume/live"
    )


def test_llm_responses_endpoint(monkeypatch):
    cap = _run(
        monkeypatch, lambda c: c.llm_responses("what is a simple routine")
    )
    assert cap["url"].endswith("/ai_optimization/chat_gpt/llm_responses/live")


def test_llm_responses_model_in_path(monkeypatch):
    cap = _run(
        monkeypatch,
        lambda c: c.llm_responses("what is a simple routine", model="gemini"),
    )
    assert "/ai_optimization/gemini/llm_responses/live" in cap["url"]


def test_llm_mentions_endpoint(monkeypatch):
    cap = _run(monkeypatch, lambda c: c.llm_mentions("Lumen Skin"))
    assert "ai_optimization" in cap["url"]
    assert cap["url"].endswith("/live")


def test_ranked_keywords_endpoint(monkeypatch):
    cap = _run(monkeypatch, lambda c: c.ranked_keywords("lumenskin.com"))
    assert cap["url"].endswith("/dataforseo_labs/google/ranked_keywords/live")


def test_serp_competitors_endpoint(monkeypatch):
    cap = _run(monkeypatch, lambda c: c.serp_competitors(["skincare routine"]))
    assert cap["url"].endswith("/dataforseo_labs/google/serp_competitors/live")


def test_llm_scraper_endpoint(monkeypatch):
    cap = _run(monkeypatch, lambda c: c.llm_scraper("what is a simple routine"))
    assert cap["url"].endswith("/ai_optimization/chat_gpt/llm_scraper/live")


def test_post_returns_parsed_json(monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setattr(
        dataforseo.urllib.request,
        "urlopen",
        _capture_urlopen({}, {"tasks": [{"result": [{"keyword": "x"}]}]}),
    )
    out = dataforseo.DataForSEOClient().keyword_ideas(["skincare routine"])
    assert out["tasks"][0]["result"][0]["keyword"] == "x"
