"""Tests for Station 2 — Studio brand_qc.

Verifies the pure scoring function gates at 85, a clean render passes to
qc_review, and an off-brand render routes to needs_revision. No vision model.
"""
import db as db_module


def _fresh_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "t.db"))
    db_module.init_db()


def _rendered_post():
    pid = db_module.create_post(client="lumen-skin", seed_idea="seed")
    db_module.advance(
        pid,
        db_module.Status.DRAFTED,
        hook="A short clean hook.",
        body="A calm, short body.",
        image_path="renders/fake.png",
    )
    return pid


def test_score_image_clean_passes_threshold():
    from engine.studio.brand_qc import score_image, PASS_THRESHOLD

    score, notes = score_image(off_brand=False)
    assert score >= PASS_THRESHOLD
    assert isinstance(notes, str)


def test_score_image_off_brand_fails_threshold():
    from engine.studio.brand_qc import score_image, PASS_THRESHOLD

    score, notes = score_image(off_brand=True)
    assert score < PASS_THRESHOLD
    assert "brand" in notes.lower() or "violation" in notes.lower()


def test_run_clean_advances_to_qc_review(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    from engine.studio import brand_qc

    pid = _rendered_post()
    brand_qc.run(pid)
    row = db_module.get_post(pid)
    assert row["status"] == "qc_review"
    assert row["qc_score"] >= brand_qc.PASS_THRESHOLD


def test_run_off_brand_routes_to_needs_revision(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    from engine.studio import brand_qc

    pid = _rendered_post()
    # Force the off-brand branch deterministically.
    monkeypatch.setattr(brand_qc, "_detect_off_brand", lambda post: True)
    brand_qc.run(pid)
    row = db_module.get_post(pid)
    assert row["status"] == "needs_revision"
    assert row["qc_score"] < brand_qc.PASS_THRESHOLD
