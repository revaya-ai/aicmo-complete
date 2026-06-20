"""Tests for the Google Search Console client (engine/integrations/gsc.py).

The client is stdlib only (urllib + json). It never makes a real network call.
These tests monkeypatch urllib.request.urlopen so no socket is ever opened, and
assert the request the client would have sent: the endpoint with the URL-encoded
property in the path, the Bearer auth header built from the env token, and the
body shape Google expects (startDate, endDate, dimensions, rowLimit).

When the env vars are unset the client is not configured: is_configured() is
False and every method raises GSCNotConfigured before touching the network.
"""

import json

import pytest

from engine.integrations import gsc


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


def _configure(monkeypatch, token="ya29.fake-access-token", site="https://lumenskin.com/"):
    monkeypatch.setenv("GSC_ACCESS_TOKEN", token)
    monkeypatch.setenv("GSC_SITE_URL", site)


# ---- is_configured -----------------------------------------------------------


def test_not_configured_when_env_unset(monkeypatch):
    monkeypatch.delenv("GSC_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("GSC_SITE_URL", raising=False)
    assert gsc.GSCClient().is_configured() is False


def test_not_configured_when_only_token_set(monkeypatch):
    monkeypatch.setenv("GSC_ACCESS_TOKEN", "ya29.fake")
    monkeypatch.delenv("GSC_SITE_URL", raising=False)
    assert gsc.GSCClient().is_configured() is False


def test_not_configured_when_only_site_set(monkeypatch):
    monkeypatch.delenv("GSC_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("GSC_SITE_URL", "https://lumenskin.com/")
    assert gsc.GSCClient().is_configured() is False


def test_not_configured_when_var_empty(monkeypatch):
    monkeypatch.setenv("GSC_ACCESS_TOKEN", "ya29.fake")
    monkeypatch.setenv("GSC_SITE_URL", "")
    assert gsc.GSCClient().is_configured() is False


def test_configured_when_both_set(monkeypatch):
    _configure(monkeypatch)
    assert gsc.GSCClient().is_configured() is True


# ---- methods raise when not configured (no network) --------------------------


def test_methods_raise_when_not_configured(monkeypatch):
    monkeypatch.delenv("GSC_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("GSC_SITE_URL", raising=False)
    # If the method tried the network, this would blow up loudly instead.
    monkeypatch.setattr(
        gsc.urllib.request,
        "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network was called")),
    )
    client = gsc.GSCClient()
    with pytest.raises(gsc.GSCNotConfigured):
        client.search_analytics("2024-01-01", "2024-12-31")


# ---- auth header + request shape ---------------------------------------------


def test_bearer_auth_header_built_from_env(monkeypatch):
    _configure(monkeypatch, token="ya29.topsecret")
    captured = {}
    monkeypatch.setattr(
        gsc.urllib.request, "urlopen", _capture_urlopen(captured, {"rows": []})
    )
    gsc.GSCClient().search_analytics("2024-01-01", "2024-12-31")

    headers = {k.lower(): v for k, v in captured["headers"].items()}
    assert headers["authorization"] == "Bearer ya29.topsecret"
    assert "application/json" in headers["content-type"]


def test_site_url_is_encoded_in_path(monkeypatch):
    _configure(monkeypatch, site="https://lumenskin.com/")
    captured = {}
    monkeypatch.setattr(
        gsc.urllib.request, "urlopen", _capture_urlopen(captured, {"rows": []})
    )
    gsc.GSCClient().search_analytics("2024-01-01", "2024-12-31")

    # The property url is URL-encoded into the path segment.
    assert "https%3A%2F%2Flumenskin.com%2F" in captured["url"]
    assert captured["url"].endswith("/searchAnalytics/query")
    assert captured["url"].startswith(
        "https://www.googleapis.com/webmasters/v3/sites/"
    )
    assert captured["method"] == "POST"


def test_body_shape(monkeypatch):
    _configure(monkeypatch)
    captured = {}
    monkeypatch.setattr(
        gsc.urllib.request, "urlopen", _capture_urlopen(captured, {"rows": []})
    )
    gsc.GSCClient().search_analytics(
        "2024-03-01", "2024-03-31", dimensions=["query", "page"], row_limit=10
    )

    body = json.loads(captured["body"].decode("utf-8"))
    assert body["startDate"] == "2024-03-01"
    assert body["endDate"] == "2024-03-31"
    assert body["dimensions"] == ["query", "page"]
    assert body["rowLimit"] == 10


def test_body_defaults_to_query_dimension(monkeypatch):
    _configure(monkeypatch)
    captured = {}
    monkeypatch.setattr(
        gsc.urllib.request, "urlopen", _capture_urlopen(captured, {"rows": []})
    )
    gsc.GSCClient().search_analytics("2024-01-01", "2024-12-31")

    body = json.loads(captured["body"].decode("utf-8"))
    assert body["dimensions"] == ["query"]
    assert body["rowLimit"] == 25


def test_search_analytics_returns_parsed_json(monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setattr(
        gsc.urllib.request,
        "urlopen",
        _capture_urlopen({}, {"rows": [{"keys": ["simple skincare routine"]}]}),
    )
    out = gsc.GSCClient().search_analytics("2024-01-01", "2024-12-31")
    assert out["rows"][0]["keys"][0] == "simple skincare routine"
