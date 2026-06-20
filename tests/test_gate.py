"""Tests for Station 3: Mission gate.

Verifies approve/reject logic without importing Flask. The Flask app is only
constructed inside create_app(), never at module load, so these run offline.
"""
import db as db_module


def _fresh_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "t.db"))
    db_module.init_db()


def _qc_review_post():
    pid = db_module.create_post(client="lumen-skin", seed_idea="seed")
    db_module.advance(pid, db_module.Status.QC_REVIEW, qc_score=90)
    return pid


def test_run_auto_approve_advances_to_approved(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    from engine.mission import gate

    pid = _qc_review_post()
    gate.run(pid, auto_approve=True)
    row = db_module.get_post(pid)
    assert row["status"] == "approved"
    assert row["human_note"]


def test_approve_helper_advances(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    from engine.mission import gate

    pid = _qc_review_post()
    gate.approve(pid, note="ship it")
    row = db_module.get_post(pid)
    assert row["status"] == "approved"
    assert row["human_note"] == "ship it"


def test_reject_helper_sends_back_with_note(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    from engine.mission import gate

    pid = _qc_review_post()
    gate.reject(pid, note="off voice in line two")
    row = db_module.get_post(pid)
    assert row["status"] == "rejected"
    assert row["human_note"] == "off voice in line two"


def test_run_without_auto_approve_raises(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    from engine.mission import gate

    pid = _qc_review_post()
    raised = False
    try:
        gate.run(pid, auto_approve=False)
    except RuntimeError:
        raised = True
    assert raised
