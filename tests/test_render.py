"""Tests for Station 2 — Studio render.

Verifies render.py fills the template, writes a REAL placeholder PNG to disk at
the right dimensions, and sets image_path on the row. Stdlib only, no Playwright.
"""
import struct

import db as db_module


def _fresh_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "t.db"))
    db_module.init_db()


def _drafted_post(client="lumen-skin"):
    pid = db_module.create_post(client=client, seed_idea="seed")
    db_module.advance(
        pid,
        db_module.Status.DRAFTED,
        pillar="Education",
        angle="The simpler truth",
        hook="Most skincare sounds identical for one reason.",
        body="Pick three things. Do them daily. Give it four weeks.",
    )
    return pid


def _png_dimensions(path):
    with open(path, "rb") as fh:
        header = fh.read(24)
    assert header[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG file"
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def test_render_writes_real_png_and_sets_image_path(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    from engine.studio import render

    monkeypatch.setattr(render, "RENDERS_DIR", str(tmp_path / "renders"))
    pid = _drafted_post()
    render.run(pid)

    row = db_module.get_post(pid)
    assert row["image_path"], "image_path not set"
    import os

    assert os.path.exists(row["image_path"]), "PNG file not written to disk"
    width, height = _png_dimensions(row["image_path"])
    assert (width, height) == (1080, 1350)


def test_render_keeps_status_drafted(monkeypatch, tmp_path):
    _fresh_db(monkeypatch, tmp_path)
    from engine.studio import render

    monkeypatch.setattr(render, "RENDERS_DIR", str(tmp_path / "renders"))
    pid = _drafted_post()
    render.run(pid)
    assert db_module.get_post(pid)["status"] == "drafted"


def test_fill_template_substitutes_hook_and_body(monkeypatch, tmp_path):
    from engine.studio import render

    html = render.fill_template("MY HOOK LINE", "my body text")
    assert "MY HOOK LINE" in html
    assert "my body text" in html


def test_render_image_is_non_trivial(monkeypatch, tmp_path):
    """The rendered PNG must not be a uniform blank canvas. When PIL is present,
    text is actually drawn (dark ink pixels against the light background)."""
    _fresh_db(monkeypatch, tmp_path)
    from engine.studio import render

    monkeypatch.setattr(render, "RENDERS_DIR", str(tmp_path / "renders"))
    pid = _drafted_post()
    render.run(pid)
    path = db_module.get_post(pid)["image_path"]

    try:
        from PIL import Image
    except ImportError:
        # No PIL: stdlib placeholder path. Assert it is at least a real PNG.
        width, height = _png_dimensions(path)
        assert (width, height) == (1080, 1350)
        return

    img = Image.open(path).convert("RGB")
    colors = img.getcolors(maxcolors=1_000_000)
    assert colors is not None and len(colors) > 1, "image is a uniform blank canvas"
    # Text pixels: dark ink against the warm off-white background.
    dark = sum(1 for r, g, b in img.resize((216, 270)).getdata() if r + g + b < 300)
    assert dark > 50, "no text pixels drawn onto the render"
