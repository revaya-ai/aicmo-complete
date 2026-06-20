"""Tests for Station 3: Mission publish_check.

Verifies the live verification runs without error, returns True in stub mode, and
leaves status unchanged (it only logs).
"""
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


def test_check_returns_true_in_stub(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    monkeypatch.delenv("ZERNIO_API_KEY", raising=False)
    from engine.mission import publish_check

    pid = _published_post()
    assert publish_check.check(pid) is True


def test_run_leaves_status_published(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    monkeypatch.delenv("ZERNIO_API_KEY", raising=False)
    from engine.mission import publish_check

    pid = _published_post()
    publish_check.run(pid)
    assert db_module.get_post(pid)["status"] == "published"
