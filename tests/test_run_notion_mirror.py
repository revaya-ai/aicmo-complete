"""The end-to-end loop must produce outputs/notion-mirror.json itself, not only
when the mirror module is run separately. Offline, stub mode."""
import json
import sys

import db as db_module


def test_full_loop_writes_notion_mirror(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "t.db"))

    # Point the renderer and the mirror at the tmp dir so we touch no repo files.
    from engine.studio import render
    from engine.dashboard import notion_mirror

    monkeypatch.setattr(render, "RENDERS_DIR", str(tmp_path / "renders"))
    mirror_path = str(tmp_path / "notion-mirror.json")
    monkeypatch.setattr(notion_mirror, "MIRROR_PATH", mirror_path)
    monkeypatch.delenv("NOTION_TOKEN", raising=False)

    import run

    monkeypatch.setattr(sys, "argv", ["run.py", "why competitors all sound the same"])
    run.main()

    import os

    assert os.path.exists(mirror_path), "loop did not write the notion mirror"
    board = json.loads(open(mirror_path, encoding="utf-8").read())
    assert board["mode"] == "stub"
    assert board["cards"], "mirror board has no cards"
    # The single post should have walked to ad_live.
    assert any(c["status"] == "ad_live" for c in board["cards"])
