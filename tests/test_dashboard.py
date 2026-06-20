"""Tests for the dashboard + reporting layer.

metrics.py aggregates the pipeline. report.py renders a weekly markdown brief.
notion_mirror.py writes a JSON board (stub) when no NOTION_TOKEN is set, and can
mirror qc_review items for the "approve from your phone" human gate.

Offline, stdlib only.
"""
import json

import db as db_module


def _fresh_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "t.db"))
    db_module.init_db()


def _post_at(status, client="lumen-skin", **fields):
    pid = db_module.create_post(client=client, seed_idea="seed")
    db_module.advance(pid, status, **fields)
    return pid


# ---- metrics --------------------------------------------------------------

def test_metrics_counts_by_status(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    from engine.dashboard import metrics

    _post_at(db_module.Status.DRAFTED, hook="h", body="b")
    _post_at(db_module.Status.DRAFTED, hook="h", body="b")
    _post_at(db_module.Status.PUBLISHED, hook="h", body="b", published_url="http://x")

    summary = metrics.summarize()
    assert summary["counts_by_status"]["drafted"] == 2
    assert summary["counts_by_status"]["published"] == 1
    assert summary["total_posts"] == 3
    assert "run_cost_usd" in summary


def test_metrics_top_posts_ranked(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    from engine.dashboard import metrics

    high = {"likes": 200, "comments": 40, "shares": 20, "follows": 30, "impressions": 4000}
    low = {"likes": 2, "comments": 0, "shares": 0, "follows": 1, "impressions": 9000}
    _post_at(db_module.Status.ANALYZED, hook="winner", body="b", metrics_json=json.dumps(high))
    _post_at(db_module.Status.ANALYZED, hook="loser", body="b", metrics_json=json.dumps(low))

    summary = metrics.summarize()
    assert summary["top_posts"][0]["hook"] == "winner"


# ---- report ---------------------------------------------------------------

def test_report_writes_markdown(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    from engine.dashboard import report

    _post_at(db_module.Status.PUBLISHED, hook="h", body="b", published_url="http://x")
    out = tmp_path / "brief.md"
    path = report.write_report(str(out))
    assert path == str(out)
    assert out.exists()
    text = out.read_text()
    assert "Weekly brief" in text
    assert "published" in text


# ---- notion mirror --------------------------------------------------------

def test_notion_mirror_stub_writes_json(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    from engine.dashboard import notion_mirror

    _post_at(db_module.Status.QC_REVIEW, hook="needs review", body="b", qc_score=90)
    out = tmp_path / "notion-mirror.json"
    path = notion_mirror.mirror(str(out))
    assert path == str(out)
    board = json.loads(out.read_text())
    assert board["mode"] == "stub"
    assert any(card["hook"] == "needs review" for card in board["cards"])


def test_notion_mirror_qc_review_only_filter(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    from engine.dashboard import notion_mirror

    _post_at(db_module.Status.QC_REVIEW, hook="gate me", body="b", qc_score=90)
    _post_at(db_module.Status.DRAFTED, hook="not ready", body="b")
    out = tmp_path / "gate.json"
    notion_mirror.mirror_gate(str(out))
    board = json.loads(out.read_text())
    hooks = {c["hook"] for c in board["cards"]}
    assert "gate me" in hooks
    assert "not ready" not in hooks
