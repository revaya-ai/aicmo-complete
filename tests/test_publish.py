"""Tests for Station 3: Mission publish.

Verifies a scheduled post advances to published with a URL, in stub mode.
"""
import db as db_module


def _fresh_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "t.db"))
    db_module.init_db()


def _scheduled_post():
    pid = db_module.create_post(client="lumen-skin", seed_idea="seed")
    db_module.advance(
        pid,
        db_module.Status.SCHEDULED,
        hook="A hook",
        body="A body",
        image_path="renders/x.png",
        scheduled_for="2026-06-22T09:00:00",
    )
    return pid


def test_publish_advances_and_sets_url(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    monkeypatch.delenv("ZERNIO_API_KEY", raising=False)
    from engine.mission import publish

    pid = _scheduled_post()
    publish.run(pid)
    row = db_module.get_post(pid)
    assert row["status"] == "published"
    assert row["published_url"].startswith("http")
