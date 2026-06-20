"""Tests for Station 4: Ads agent and push.

Verifies a high-engagement post becomes ad_recommended, a low one stays
analyzed, the spend gate advances ad_recommended -> ad_approved, and the push
takes ad_approved -> ad_live with a fake campaign id (stub mode, no tokens).
"""
import json

import db as db_module


def _fresh_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "t.db"))
    db_module.init_db()


def _analyzed_post(metrics):
    pid = db_module.create_post(client="lumen-skin", seed_idea="seed")
    db_module.advance(
        pid,
        db_module.Status.ANALYZED,
        hook="A hook",
        body="A body",
        metrics_json=json.dumps(metrics),
    )
    return pid


HIGH = {"likes": 180, "comments": 40, "shares": 22, "follows": 38, "impressions": 4000}
LOW = {"likes": 5, "comments": 1, "shares": 0, "follows": 2, "impressions": 8000}


def test_is_winner_true_for_high_engagement():
    from engine.ads.ads_agent import is_winner

    assert is_winner(HIGH) is True


def test_is_winner_false_for_low_engagement():
    from engine.ads.ads_agent import is_winner

    assert is_winner(LOW) is False


def test_run_high_engagement_reaches_ad_live(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    monkeypatch.delenv("META_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("LINKEDIN_ACCESS_TOKEN", raising=False)
    from engine.ads import ads_agent

    pid = _analyzed_post(HIGH)
    ads_agent.run(pid, auto_approve=True)
    row = db_module.get_post(pid)
    assert row["status"] == "ad_live"
    assert row["ad_status"].startswith("live:")
    assert row["ad_spend_approved_by"]
    assert row["ad_budget"] > 0


def test_run_low_engagement_stays_analyzed(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    from engine.ads import ads_agent

    pid = _analyzed_post(LOW)
    ads_agent.run(pid, auto_approve=True)
    assert db_module.get_post(pid)["status"] == "analyzed"


def test_run_high_engagement_no_auto_stops_at_recommended(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    from engine.ads import ads_agent

    pid = _analyzed_post(HIGH)
    ads_agent.run(pid, auto_approve=False)
    assert db_module.get_post(pid)["status"] == "ad_recommended"


def test_push_advances_approved_to_live(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    monkeypatch.delenv("META_ACCESS_TOKEN", raising=False)
    from engine.ads import ads_push

    pid = _analyzed_post(HIGH)
    db_module.advance(
        pid,
        db_module.Status.AD_APPROVED,
        ad_budget=50.0,
        ad_audience="Women 25-45",
        ad_spend_approved_by="AUTO",
    )
    ads_push.run(pid)
    row = db_module.get_post(pid)
    assert row["status"] == "ad_live"
    assert row["ad_status"].startswith("live:")
