"""Tests for the Backblaze B2 client (engine/integrations/backblaze.py).

The client is stdlib only (urllib + base64 + json). It never makes a real
network call. These tests monkeypatch urllib.request.urlopen so no socket is
ever opened, and assert the request the client would have sent: the auth
handshake header built from the env credentials, and that the upload sends the
file bytes to the upload url returned by the handshake.

When the env vars are unset the client is not configured: is_configured() is
False and every method raises BackblazeNotConfigured before touching the
network, so no socket is opened and no bytes leave the machine.
"""

import base64
import json

import pytest

from engine.integrations import backblaze


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


def _capture_urlopen(captured: dict, payloads):
    """Build a fake urlopen that records each Request and returns payloads in order."""
    calls = captured.setdefault("calls", [])
    queue = list(payloads)

    def fake_urlopen(req, timeout=None):
        calls.append(
            {
                "url": req.full_url,
                "headers": {k.lower(): v for k, v in req.header_items()},
                "body": req.data,
                "method": req.get_method(),
            }
        )
        return _FakeResponse(queue.pop(0))

    return fake_urlopen


def _configure(monkeypatch, key_id="key-id-123", app_key="app-key-456", bucket="b2-bucket"):
    monkeypatch.setenv("BACKBLAZE_KEY_ID", key_id)
    monkeypatch.setenv("BACKBLAZE_APPLICATION_KEY", app_key)
    monkeypatch.setenv("BACKBLAZE_BUCKET", bucket)


# ---- is_configured -----------------------------------------------------------


def test_not_configured_when_env_unset(monkeypatch):
    monkeypatch.delenv("BACKBLAZE_KEY_ID", raising=False)
    monkeypatch.delenv("BACKBLAZE_APPLICATION_KEY", raising=False)
    monkeypatch.delenv("BACKBLAZE_BUCKET", raising=False)
    assert backblaze.BackblazeClient().is_configured() is False


def test_not_configured_when_only_some_vars_set(monkeypatch):
    monkeypatch.setenv("BACKBLAZE_KEY_ID", "key-id-123")
    monkeypatch.delenv("BACKBLAZE_APPLICATION_KEY", raising=False)
    monkeypatch.delenv("BACKBLAZE_BUCKET", raising=False)
    assert backblaze.BackblazeClient().is_configured() is False


def test_not_configured_when_var_empty(monkeypatch):
    monkeypatch.setenv("BACKBLAZE_KEY_ID", "key-id-123")
    monkeypatch.setenv("BACKBLAZE_APPLICATION_KEY", "")
    monkeypatch.setenv("BACKBLAZE_BUCKET", "b2-bucket")
    assert backblaze.BackblazeClient().is_configured() is False


def test_configured_when_all_set(monkeypatch):
    _configure(monkeypatch)
    assert backblaze.BackblazeClient().is_configured() is True


# ---- methods raise when not configured (no network) --------------------------


def test_backup_file_raises_when_not_configured(monkeypatch, tmp_path):
    monkeypatch.delenv("BACKBLAZE_KEY_ID", raising=False)
    monkeypatch.delenv("BACKBLAZE_APPLICATION_KEY", raising=False)
    monkeypatch.delenv("BACKBLAZE_BUCKET", raising=False)
    # If anything tried the network, this would blow up loudly instead.
    monkeypatch.setattr(
        backblaze.urllib.request,
        "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network was called")),
    )
    local = tmp_path / "f.txt"
    local.write_text("payload")
    client = backblaze.BackblazeClient()
    with pytest.raises(backblaze.BackblazeNotConfigured):
        client.backup_file(str(local), "remote/f.txt")


# ---- auth handshake header ---------------------------------------------------


def test_authorize_basic_auth_header_built_from_env(monkeypatch, tmp_path):
    _configure(monkeypatch, "myKeyId", "myAppKey", "bucket")
    captured = {}
    handshake = {
        "authorizationToken": "auth-token-abc",
        "apiUrl": "https://api.backblaze.test",
    }
    upload_creds = {
        "uploadUrl": "https://upload.backblaze.test/upload",
        "authorizationToken": "upload-token-xyz",
    }
    upload_result = {"fileId": "file-789"}
    monkeypatch.setattr(
        backblaze.urllib.request,
        "urlopen",
        _capture_urlopen(captured, [handshake, upload_creds, upload_result]),
    )
    local = tmp_path / "artifact.txt"
    local.write_text("the bytes")

    backblaze.BackblazeClient().backup_file(str(local), "remote/artifact.txt")

    first = captured["calls"][0]
    expected = base64.b64encode(b"myKeyId:myAppKey").decode("ascii")
    assert first["headers"]["authorization"] == f"Basic {expected}"
    assert first["url"].endswith("/b2api/v3/b2_authorize_account")


def test_backup_file_uploads_to_handshake_url(monkeypatch, tmp_path):
    _configure(monkeypatch)
    captured = {}
    handshake = {
        "authorizationToken": "auth-token-abc",
        "apiUrl": "https://api.backblaze.test",
    }
    upload_creds = {
        "uploadUrl": "https://upload.backblaze.test/upload",
        "authorizationToken": "upload-token-xyz",
    }
    upload_result = {"fileId": "file-789", "fileName": "remote/artifact.txt"}
    monkeypatch.setattr(
        backblaze.urllib.request,
        "urlopen",
        _capture_urlopen(captured, [handshake, upload_creds, upload_result]),
    )
    local = tmp_path / "artifact.txt"
    local.write_bytes(b"the bytes")

    out = backblaze.BackblazeClient().backup_file(str(local), "remote/artifact.txt")

    upload_call = captured["calls"][-1]
    assert upload_call["url"] == "https://upload.backblaze.test/upload"
    assert upload_call["headers"]["authorization"] == "upload-token-xyz"
    assert upload_call["body"] == b"the bytes"
    assert out["fileId"] == "file-789"
