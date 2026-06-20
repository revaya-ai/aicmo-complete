import db as db_module


def _fresh_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "t.db"))
    db_module.init_db()


def test_save_draft_creates_drafted_record(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    from engine.save_draft import save_draft

    pid = save_draft(
        client="lumen-skin",
        seed_idea="why competitors all sound the same",
        pillar="Education",
        angle="The simpler truth",
        hook="Most skincare brands sound identical for one reason.",
        body="Here is what actually moves the needle.\n\nPick three things. Do them daily.",
    )
    row = db_module.get_post(pid)
    assert row["status"] == "drafted"
    assert row["pillar"] == "Education"
    assert row["angle"] == "The simpler truth"
    assert row["hook"].startswith("Most skincare brands")
    assert "moves the needle" in row["body"]
    assert row["client"] == "lumen-skin"
