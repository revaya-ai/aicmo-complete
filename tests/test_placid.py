"""Tests for the Placid client (engine/integrations/placid.py).

The client is stdlib only (urllib + json). It never makes a real network call.
These tests monkeypatch urllib.request.urlopen so no socket is ever opened, and
assert the request the client would have sent: the endpoint, the Bearer auth
header built from the env token, and that the body is the JSON Placid expects
(a dict with template_uuid and layers).

When the env var is unset the client is not configured: is_configured() is False
and every method raises PlacidNotConfigured before touching the network.
"""

import json

import pytest

from engine.integrations import placid


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


def _configure(monkeypatch, token="placid-token-123"):
    monkeypatch.setenv("PLACID_API_TOKEN", token)


# ---- is_configured -----------------------------------------------------------


def test_not_configured_when_env_unset(monkeypatch):
    monkeypatch.delenv("PLACID_API_TOKEN", raising=False)
    client = placid.PlacidClient()
    assert client.is_configured() is False


def test_not_configured_when_var_empty(monkeypatch):
    monkeypatch.setenv("PLACID_API_TOKEN", "")
    assert placid.PlacidClient().is_configured() is False


def test_configured_when_token_set(monkeypatch):
    _configure(monkeypatch)
    assert placid.PlacidClient().is_configured() is True


# ---- methods raise when not configured (no network) --------------------------


def test_methods_raise_when_not_configured(monkeypatch):
    monkeypatch.delenv("PLACID_API_TOKEN", raising=False)
    # If any method tried the network, this would blow up loudly instead.
    monkeypatch.setattr(
        placid.urllib.request,
        "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network was called")),
    )
    client = placid.PlacidClient()
    with pytest.raises(placid.PlacidNotConfigured):
        client.render_image("tpl-uuid", {"hook": {"text": "x"}})
    with pytest.raises(placid.PlacidNotConfigured):
        client.get_image("img-123")


# ---- auth header + request shape ---------------------------------------------


def test_bearer_auth_header_built_from_env(monkeypatch):
    _configure(monkeypatch, "secret-bearer")
    captured = {}
    monkeypatch.setattr(
        placid.urllib.request, "urlopen", _capture_urlopen(captured, {"status": "queued"})
    )
    client = placid.PlacidClient()
    client.render_image("tpl-uuid", {"hook": {"text": "Hello"}})

    headers = {k.lower(): v for k, v in captured["headers"].items()}
    assert headers["authorization"] == "Bearer secret-bearer"
    assert "application/json" in headers["content-type"]


def test_render_image_body_shape(monkeypatch):
    _configure(monkeypatch)
    captured = {}
    monkeypatch.setattr(
        placid.urllib.request, "urlopen", _capture_urlopen(captured, {"status": "queued"})
    )
    client = placid.PlacidClient()
    client.render_image("tpl-uuid", {"hook": {"text": "Hello"}})

    body = json.loads(captured["body"].decode("utf-8"))
    assert isinstance(body, dict)
    assert body["template_uuid"] == "tpl-uuid"
    assert body["layers"] == {"hook": {"text": "Hello"}}
    assert captured["method"] == "POST"


# ---- endpoints ---------------------------------------------------------------


def test_render_image_endpoint(monkeypatch):
    _configure(monkeypatch)
    captured = {}
    monkeypatch.setattr(
        placid.urllib.request, "urlopen", _capture_urlopen(captured, {"status": "queued"})
    )
    placid.PlacidClient().render_image("tpl-uuid", {})
    assert captured["url"].endswith("/images")
    assert captured["url"].startswith("https://api.placid.app/api/rest/")


def test_get_image_endpoint(monkeypatch):
    _configure(monkeypatch)
    captured = {}
    monkeypatch.setattr(
        placid.urllib.request, "urlopen", _capture_urlopen(captured, {"status": "finished"})
    )
    placid.PlacidClient().get_image("img-123")
    assert captured["url"].endswith("/images/img-123")
    assert captured["method"] == "GET"


def test_render_image_uses_default_template_uuid_from_env(monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setenv("PLACID_TEMPLATE_UUID", "env-tpl-uuid")
    captured = {}
    monkeypatch.setattr(
        placid.urllib.request, "urlopen", _capture_urlopen(captured, {"status": "queued"})
    )
    placid.PlacidClient().render_image(None, {"hook": {"text": "x"}})
    body = json.loads(captured["body"].decode("utf-8"))
    assert body["template_uuid"] == "env-tpl-uuid"


def test_render_image_returns_parsed_json(monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setattr(
        placid.urllib.request,
        "urlopen",
        _capture_urlopen({}, {"status": "finished", "image_url": "https://x/y.png"}),
    )
    out = placid.PlacidClient().render_image("tpl-uuid", {})
    assert out["status"] == "finished"
    assert out["image_url"] == "https://x/y.png"
