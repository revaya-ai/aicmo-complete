"""Tests for Station 3: Mission schedule.

Verifies an approved post gets a future scheduled_for at a weekday 09:00 slot
and advances to scheduled.
"""
from datetime import datetime

import db as db_module


def _fresh_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "t.db"))
    db_module.init_db()


def _approved_post():
    pid = db_module.create_post(client="lumen-skin", seed_idea="seed")
    db_module.advance(pid, db_module.Status.APPROVED)
    return pid


def test_next_slot_is_a_weekday_at_nine():
    from engine.mission.schedule import next_slot

    # A Saturday should roll forward to Monday 09:00.
    saturday = datetime(2026, 6, 20, 14, 0, 0)  # 2026-06-20 is a Saturday
    slot = next_slot(saturday)
    assert slot.hour == 9 and slot.minute == 0
    assert slot.weekday() < 5  # Mon-Fri
    assert slot > saturday


def test_run_schedules_future_and_advances(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    from engine.mission import schedule

    pid = _approved_post()
    schedule.run(pid)
    row = db_module.get_post(pid)
    assert row["status"] == "scheduled"
    assert row["scheduled_for"]
    when = datetime.fromisoformat(row["scheduled_for"])
    assert when > datetime.utcnow()
    assert when.hour == 9
