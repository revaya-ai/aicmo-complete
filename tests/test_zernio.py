"""Tests for Station 3: Zernio client.

Verifies the stub returns a fake URL with no API key set, and never crashes.
No network.
"""


def test_publish_stub_returns_url_without_key(monkeypatch):
    monkeypatch.delenv("ZERNIO_API_KEY", raising=False)
    from engine.mission import zernio

    result = zernio.publish_post(
        image_path="renders/x.png",
        hook="A hook",
        body="A body",
        platform="linkedin",
    )
    assert result["url"].startswith("http")
    assert result["mode"] == "stub"


def test_is_live_stub_true():
    from engine.mission import zernio

    assert zernio.is_live("https://example.test/abc") is True
