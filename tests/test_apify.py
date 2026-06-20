"""Tests for the Apify client (engine/integrations/apify.py).

The client is stdlib only (urllib + json). It never makes a real network call.
These tests monkeypatch urllib.request.urlopen so no socket is ever opened, and
assert the request the client would have sent: the run-sync-get-dataset-items
endpoint, the Bearer auth header in the header (never in the URL query string),
and the run_input body. Apify returns a JSON array of dataset items, so a list
parses through and an odd shape degrades to [].

When the token is unset the client is not configured: is_configured() is False
and every method raises ApifyNotConfigured before touching the network.
"""

import json

import pytest

from engine.integrations import apify


class _FakeResponse:
    """Minimal stand-in for the object urllib.request.urlopen returns."""

    def __init__(self, payload):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _capture_urlopen(captured: dict, payload):
    """Build a fake urlopen that records the Request it was handed."""

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        captured["body"] = req.data
        captured["method"] = req.get_method()
        return _FakeResponse(payload)

    return fake_urlopen


def _configure(monkeypatch, token="apify_api_faketoken"):
    monkeypatch.setenv("APIFY_TOKEN", token)


# ---- is_configured -----------------------------------------------------------


def test_not_configured_when_env_unset(monkeypatch):
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    assert apify.ApifyClient().is_configured() is False


def test_not_configured_when_var_empty(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "")
    assert apify.ApifyClient().is_configured() is False


def test_configured_when_set(monkeypatch):
    _configure(monkeypatch)
    assert apify.ApifyClient().is_configured() is True


# ---- methods raise when not configured (no network) --------------------------


def test_methods_raise_when_not_configured(monkeypatch):
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    # If the method tried the network, this would blow up loudly instead.
    monkeypatch.setattr(
        apify.urllib.request,
        "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network was called")),
    )
    client = apify.ApifyClient()
    with pytest.raises(apify.ApifyNotConfigured):
        client.run_actor_get_items("apify/instagram-scraper", {"resultsLimit": 5})


# ---- auth header + request shape ---------------------------------------------


def test_bearer_auth_header_built_from_env(monkeypatch):
    _configure(monkeypatch, token="apify_api_topsecret")
    captured = {}
    monkeypatch.setattr(
        apify.urllib.request, "urlopen", _capture_urlopen(captured, [])
    )
    apify.ApifyClient().run_actor_get_items("apify/web-scraper", {"x": 1})

    headers = {k.lower(): v for k, v in captured["headers"].items()}
    assert headers["authorization"] == "Bearer apify_api_topsecret"
    assert "application/json" in headers["content-type"]


def test_token_not_in_url(monkeypatch):
    _configure(monkeypatch, token="apify_api_topsecret")
    captured = {}
    monkeypatch.setattr(
        apify.urllib.request, "urlopen", _capture_urlopen(captured, [])
    )
    apify.ApifyClient().run_actor_get_items("apify/web-scraper", {"x": 1})

    # The token must never ride in the URL query string.
    assert "apify_api_topsecret" not in captured["url"]
    assert "token=" not in captured["url"]


def test_endpoint_and_body(monkeypatch):
    _configure(monkeypatch)
    captured = {}
    monkeypatch.setattr(
        apify.urllib.request, "urlopen", _capture_urlopen(captured, [])
    )
    apify.ApifyClient().run_actor_get_items(
        "apify/instagram-scraper", {"resultsLimit": 25}
    )

    assert captured["url"].endswith(
        "/acts/apify/instagram-scraper/run-sync-get-dataset-items"
    )
    assert captured["url"].startswith("https://api.apify.com/v2/")
    assert captured["method"] == "POST"
    body = json.loads(captured["body"].decode("utf-8"))
    assert body == {"resultsLimit": 25}


# ---- response handling -------------------------------------------------------


def test_returns_list_of_items(monkeypatch):
    _configure(monkeypatch)
    items = [{"caption": "competitor angle one"}, {"text": "competitor angle two"}]
    monkeypatch.setattr(
        apify.urllib.request, "urlopen", _capture_urlopen({}, items)
    )
    out = apify.ApifyClient().run_actor_get_items("apify/web-scraper", {})
    assert out == items


def test_odd_shape_degrades_to_empty_list(monkeypatch):
    _configure(monkeypatch)
    # An error object (dict) instead of a list must degrade to [].
    monkeypatch.setattr(
        apify.urllib.request,
        "urlopen",
        _capture_urlopen({}, {"error": "actor failed"}),
    )
    out = apify.ApifyClient().run_actor_get_items("apify/web-scraper", {})
    assert out == []
