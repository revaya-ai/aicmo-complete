"""Tests for the feedback loop.

Harvests the top performers among analyzed posts and appends a learnings note to
client-data/<client>/learnings.md (what won and the language that won). Offline,
stdlib only.
"""
import json

import db as db_module
from engine import feedback


def _fresh_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "t.db"))
    db_module.init_db()


def _analyzed(client, hook, metrics):
    pid = db_module.create_post(client=client, seed_idea="seed")
    db_module.advance(
        pid,
        db_module.Status.ANALYZED,
        hook=hook,
        body="A body",
        pillar="Education",
        angle="An angle",
        metrics_json=json.dumps(metrics),
    )
    return pid


HIGH = {"likes": 180, "comments": 40, "shares": 22, "follows": 38, "impressions": 4000}
MID = {"likes": 60, "comments": 8, "shares": 3, "follows": 5, "impressions": 5000}
LOW = {"likes": 5, "comments": 1, "shares": 0, "follows": 2, "impressions": 8000}


def test_harvest_ranks_winners_first():
    ranked = feedback.harvest_winners(
        [
            {"hook": "low", "metrics_json": json.dumps(LOW)},
            {"hook": "high", "metrics_json": json.dumps(HIGH)},
            {"hook": "mid", "metrics_json": json.dumps(MID)},
        ]
    )
    assert ranked[0]["hook"] == "high"
    assert ranked[-1]["hook"] == "low"


def test_run_writes_learnings_file(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    learnings = tmp_path / "learnings.md"
    monkeypatch.setattr(feedback, "_learnings_path", lambda client: str(learnings))

    _analyzed("lumen-skin", "the winning hook line", HIGH)
    _analyzed("lumen-skin", "a weaker hook", LOW)

    feedback.run_for_client("lumen-skin")

    assert learnings.exists()
    text = learnings.read_text()
    assert "the winning hook line" in text
    assert "What won" in text


def test_run_appends_not_overwrites(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    learnings = tmp_path / "learnings.md"
    learnings.write_text("# Learnings\n\nExisting note.\n")
    monkeypatch.setattr(feedback, "_learnings_path", lambda client: str(learnings))

    _analyzed("lumen-skin", "the winning hook line", HIGH)
    feedback.run_for_client("lumen-skin")

    text = learnings.read_text()
    assert "Existing note." in text
    assert "the winning hook line" in text


def test_no_analyzed_posts_is_safe(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    learnings = tmp_path / "learnings.md"
    monkeypatch.setattr(feedback, "_learnings_path", lambda client: str(learnings))
    # No analyzed posts: should not crash and should report nothing harvested.
    count = feedback.run_for_client("lumen-skin")
    assert count == 0
