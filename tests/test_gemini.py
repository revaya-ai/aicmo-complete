"""Tests for the Gemini image client (engine/integrations/gemini.py).

The client is stdlib only (urllib + base64 + json). It never makes a real
network call. These tests monkeypatch urllib.request.urlopen so no socket is
ever opened, and assert the request the client would have sent: the endpoint,
the model, the x-goog-api-key header built from the env key, and that a fake
base64 inline-data response is decoded back to the expected raw image bytes.

When the env var is unset the client is not configured: is_configured() is False
and generate_image raises GeminiNotConfigured before touching the network.
"""

import base64
import json

import pytest

from engine.integrations import gemini


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


def _inline_image_payload(raw: bytes) -> dict:
    """A Gemini generateContent response carrying one inline base64 image."""
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "here is your image"},
                        {
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": base64.b64encode(raw).decode("ascii"),
                            }
                        },
                    ]
                }
            }
        ]
    }


def _configure(monkeypatch, key="gemini-key-123"):
    monkeypatch.setenv("GEMINI_API_KEY", key)


# ---- is_configured -----------------------------------------------------------


def test_not_configured_when_env_unset(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    client = gemini.GeminiImageClient()
    assert client.is_configured() is False


def test_not_configured_when_var_empty(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    assert gemini.GeminiImageClient().is_configured() is False


def test_configured_when_key_set(monkeypatch):
    _configure(monkeypatch)
    assert gemini.GeminiImageClient().is_configured() is True


# ---- generate_image raises when not configured (no network) ------------------


def test_generate_raises_when_not_configured(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    # If the method tried the network, this would blow up loudly instead.
    monkeypatch.setattr(
        gemini.urllib.request,
        "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network was called")),
    )
    client = gemini.GeminiImageClient()
    with pytest.raises(gemini.GeminiNotConfigured):
        client.generate_image("a calm editorial skincare scene")


# ---- auth header + request shape ---------------------------------------------


def test_api_key_header_built_from_env(monkeypatch):
    _configure(monkeypatch, "secret-goog-key")
    captured = {}
    monkeypatch.setattr(
        gemini.urllib.request,
        "urlopen",
        _capture_urlopen(captured, _inline_image_payload(b"img")),
    )
    client = gemini.GeminiImageClient()
    client.generate_image("hello")

    headers = {k.lower(): v for k, v in captured["headers"].items()}
    assert headers["x-goog-api-key"] == "secret-goog-key"
    assert "application/json" in headers["content-type"]
    # The key must never appear in the URL query string.
    assert "secret-goog-key" not in captured["url"]


def test_endpoint_and_model(monkeypatch):
    _configure(monkeypatch)
    captured = {}
    monkeypatch.setattr(
        gemini.urllib.request,
        "urlopen",
        _capture_urlopen(captured, _inline_image_payload(b"img")),
    )
    gemini.GeminiImageClient().generate_image("hello")

    assert captured["url"].startswith(
        "https://generativelanguage.googleapis.com/v1beta/models/"
    )
    assert "gemini-2.5-flash-image:generateContent" in captured["url"]
    assert captured["method"] == "POST"


def test_request_body_shape(monkeypatch):
    _configure(monkeypatch)
    captured = {}
    monkeypatch.setattr(
        gemini.urllib.request,
        "urlopen",
        _capture_urlopen(captured, _inline_image_payload(b"img")),
    )
    gemini.GeminiImageClient().generate_image("my prompt text")

    body = json.loads(captured["body"].decode("utf-8"))
    assert body["contents"][0]["parts"][0]["text"] == "my prompt text"


# ---- response decoding -------------------------------------------------------


def test_inline_data_decoded_to_bytes(monkeypatch):
    _configure(monkeypatch)
    raw = b"\x89PNG\r\n\x1a\n-some-fake-image-bytes-"
    monkeypatch.setattr(
        gemini.urllib.request,
        "urlopen",
        _capture_urlopen({}, _inline_image_payload(raw)),
    )
    out = gemini.GeminiImageClient().generate_image("hello")
    assert out == raw


def test_no_inline_image_raises(monkeypatch):
    _configure(monkeypatch)
    payload = {
        "candidates": [
            {"content": {"parts": [{"text": "no image here, sorry"}]}}
        ]
    }
    monkeypatch.setattr(
        gemini.urllib.request, "urlopen", _capture_urlopen({}, payload)
    )
    with pytest.raises(RuntimeError):
        gemini.GeminiImageClient().generate_image("hello")


# ---- render-level integration (gemini backend) -------------------------------


def test_default_render_is_offline_no_gemini(monkeypatch, tmp_path):
    """With no AICMO_RENDER env var, the default render path must run offline and
    must never call Gemini."""
    import db as db_module

    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "t.db"))
    db_module.init_db()
    from engine.studio import render

    monkeypatch.delenv("AICMO_RENDER", raising=False)
    monkeypatch.setattr(render, "RENDERS_DIR", str(tmp_path / "renders"))

    called = {"gemini": False}

    class _FakeClient:
        def is_configured(self):
            called["gemini"] = True
            return True

    monkeypatch.setattr(render, "_gemini_client", lambda: _FakeClient())

    pid = db_module.create_post(client="lumen-skin", seed_idea="seed")
    db_module.advance(
        pid,
        db_module.Status.DRAFTED,
        pillar="Education",
        angle="The simpler truth",
        hook="Most skincare sounds identical for one reason.",
        body="Pick three things. Do them daily. Give it four weeks.",
    )
    render.run(pid)

    assert called["gemini"] is False, "default path must not touch Gemini"
    assert db_module.get_post(pid)["image_path"], "image_path not set offline"


def test_gemini_path_taken_with_env_and_configured_client(monkeypatch, tmp_path):
    """With AICMO_RENDER=gemini and a configured client, the Gemini path runs and
    writes the returned bytes to the image file."""
    import os

    import db as db_module

    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "t.db"))
    db_module.init_db()
    from engine.studio import render

    monkeypatch.setenv("AICMO_RENDER", "gemini")
    monkeypatch.setattr(render, "RENDERS_DIR", str(tmp_path / "renders"))

    raw = b"\x89PNG\r\n\x1a\n-fake-gemini-output-"
    calls = {"generate_called": False}

    class _FakeClient:
        def is_configured(self):
            return True

        def generate_image(self, prompt):
            calls["generate_called"] = True
            calls["prompt"] = prompt
            return raw

    monkeypatch.setattr(render, "_gemini_client", lambda: _FakeClient())

    pid = db_module.create_post(client="lumen-skin", seed_idea="seed")
    db_module.advance(
        pid,
        db_module.Status.DRAFTED,
        pillar="Education",
        angle="The simpler truth",
        hook="Most skincare sounds identical for one reason.",
        body="Pick three things. Do them daily. Give it four weeks.",
    )
    render.run(pid)

    assert calls["generate_called"] is True, "Gemini generate_image not called"
    row = db_module.get_post(pid)
    assert row["image_path"], "image_path not set on Gemini path"
    assert os.path.exists(row["image_path"]), "Gemini image not written"
    with open(row["image_path"], "rb") as fh:
        assert fh.read() == raw, "Gemini bytes not written to image file"


def test_gemini_falls_back_to_offline_on_error(monkeypatch, tmp_path):
    """If the Gemini path raises, render still produces an offline image."""
    import os

    import db as db_module

    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "t.db"))
    db_module.init_db()
    from engine.studio import render

    monkeypatch.setenv("AICMO_RENDER", "gemini")
    monkeypatch.setattr(render, "RENDERS_DIR", str(tmp_path / "renders"))

    class _BoomClient:
        def is_configured(self):
            return True

        def generate_image(self, prompt):
            raise RuntimeError("gemini boom")

    monkeypatch.setattr(render, "_gemini_client", lambda: _BoomClient())

    pid = db_module.create_post(client="lumen-skin", seed_idea="seed")
    db_module.advance(
        pid,
        db_module.Status.DRAFTED,
        pillar="Education",
        angle="The simpler truth",
        hook="Most skincare sounds identical for one reason.",
        body="Pick three things. Do them daily. Give it four weeks.",
    )
    render.run(pid)

    row = db_module.get_post(pid)
    assert row["image_path"], "fallback image_path not set after Gemini error"
    assert os.path.exists(row["image_path"]), "fallback PNG not written"
