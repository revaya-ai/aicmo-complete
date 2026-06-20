"""Tests for Station 3: Mission analytics.

Verifies a published post advances to analyzed with a metrics_json payload that
parses and carries the expected keys.
"""
import json

import db as db_module


def _fresh_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "t.db"))
    db_module.init_db()


def _published_post():
    pid = db_module.create_post(client="lumen-skin", seed_idea="seed")
    db_module.advance(
        pid,
        db_module.Status.PUBLISHED,
        published_url="https://zernio.test/p/abc123",
    )
    return pid


def test_analytics_advances_and_sets_metrics(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    monkeypatch.delenv("ZERNIO_API_KEY", raising=False)
    from engine.mission import analytics

    pid = _published_post()
    analytics.run(pid)
    row = db_module.get_post(pid)
    assert row["status"] == "analyzed"
    metrics = json.loads(row["metrics_json"])
    for key in ("likes", "comments", "shares", "follows", "impressions"):
        assert key in metrics
        assert isinstance(metrics[key], int)


def test_mock_metrics_is_deterministic():
    from engine.mission.analytics import mock_metrics

    a = mock_metrics("same-url")
    b = mock_metrics("same-url")
    assert a == b
    c = mock_metrics("other-url")
    assert c != a  # different url, different mock numbers
