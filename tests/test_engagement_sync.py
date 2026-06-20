"""Tests for the engagement sync cron module (engine/mission/engagement_sync.py).

sync_engagement(client) walks every post in published or analyzed status, pulls
engagement metrics, and writes them back via the frozen db.py API. The default
path is a deterministic offline stub. Live mode only runs if a configured
analytics client is injected. These tests inject nothing, so no network call.

The module uses the frozen db.py helpers only. It never imports a network
library on the default path.
"""

import json

import db as db_module


def _fresh_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "t.db"))
    db_module.init_db()


def _published_post(url="https://zernio.test/p/abc123"):
    pid = db_module.create_post(client="lumen-skin", seed_idea="seed")
    db_module.advance(pid, db_module.Status.PUBLISHED, published_url=url)
    return pid


def test_offline_sync_writes_metrics_for_published(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    monkeypatch.delenv("ZERNIO_API_KEY", raising=False)
    from engine.mission import engagement_sync

    pid = _published_post()
    result = engagement_sync.sync_engagement("lumen-skin")

    assert result["synced"] >= 1
    row = db_module.get_post(pid)
    metrics = json.loads(row["metrics_json"])
    for key in ("likes", "comments", "shares", "follows", "impressions"):
        assert key in metrics
        assert isinstance(metrics[key], int)


def test_sync_only_touches_published_and_analyzed(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    monkeypatch.delenv("ZERNIO_API_KEY", raising=False)
    from engine.mission import engagement_sync

    captured_pid = _published_post("https://zernio.test/p/live1")
    # A drafted post must be ignored.
    draft_pid = db_module.create_post(client="lumen-skin", seed_idea="draft")
    db_module.advance(draft_pid, db_module.Status.DRAFTED)

    engagement_sync.sync_engagement("lumen-skin")

    assert db_module.get_post(captured_pid)["metrics_json"] is not None
    assert db_module.get_post(draft_pid)["metrics_json"] is None


def test_sync_scopes_to_client(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    monkeypatch.delenv("ZERNIO_API_KEY", raising=False)
    from engine.mission import engagement_sync

    mine = _published_post("https://zernio.test/p/mine")
    other = db_module.create_post(client="other-brand", seed_idea="x")
    db_module.advance(other, db_module.Status.PUBLISHED, published_url="https://zernio.test/p/other")

    result = engagement_sync.sync_engagement("lumen-skin")

    assert db_module.get_post(mine)["metrics_json"] is not None
    assert db_module.get_post(other)["metrics_json"] is None
    assert result["synced"] == 1


def test_offline_metrics_deterministic(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    monkeypatch.delenv("ZERNIO_API_KEY", raising=False)
    from engine.mission import engagement_sync

    pid = _published_post("https://zernio.test/p/stable")
    engagement_sync.sync_engagement("lumen-skin")
    first = db_module.get_post(pid)["metrics_json"]
    engagement_sync.sync_engagement("lumen-skin")
    second = db_module.get_post(pid)["metrics_json"]
    assert json.loads(first) == json.loads(second)
