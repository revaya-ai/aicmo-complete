"""Test the human gate's Notion mirror (area 4): qc_review items can be mirrored
to the notion_mirror stub so a human can approve from their phone. Offline."""
import json

import db as db_module


def _fresh_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "t.db"))
    db_module.init_db()


def test_gate_mirrors_qc_review(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    from engine.mission import gate

    pid = db_module.create_post(client="lumen-skin", seed_idea="seed")
    db_module.advance(pid, db_module.Status.QC_REVIEW, hook="approve me", body="b", qc_score=90)

    out = tmp_path / "gate-board.json"
    path = gate.mirror_to_notion(str(out))
    assert path == str(out)
    board = json.loads(out.read_text())
    assert board["mode"] == "stub"
    assert any(c["hook"] == "approve me" for c in board["cards"])
