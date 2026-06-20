"""Test the ad-creative render path (brick B4.2).

render_ad(post_id) produces an ad-sized placeholder PNG (1080x1080) and records
its path in ad_status as the creative reference. Offline, stdlib only.
"""
import db as db_module


def _fresh_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "t.db"))
    db_module.init_db()


def _png_dimensions(path):
    import struct

    with open(path, "rb") as fh:
        head = fh.read(24)
    assert head[:8] == b"\x89PNG\r\n\x1a\n"
    w, h = struct.unpack(">II", head[16:24])
    return w, h


def test_render_ad_makes_ad_sized_png(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "engine.studio.render.RENDERS_DIR", str(tmp_path / "renders")
    )
    from engine.studio import render

    pid = db_module.create_post(client="lumen-skin", seed_idea="seed")
    db_module.advance(pid, db_module.Status.ANALYZED, hook="ad hook", body="ad body")

    path = render.render_ad(pid)
    assert path.endswith(".png")
    w, h = _png_dimensions(path)
    assert (w, h) == (render.AD_WIDTH, render.AD_HEIGHT)


def test_render_ad_dimensions_are_square():
    from engine.studio import render

    assert render.AD_WIDTH == render.AD_HEIGHT == 1080
