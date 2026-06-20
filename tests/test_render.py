"""Tests for Station 2: Studio render.

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


# ---- Placid backend (optional, credential-gated) -----------------------------


def test_default_render_is_offline_no_placid(monkeypatch, tmp_path):
    """With no AICMO_RENDER env var, the default render path must run offline and
    must never call Placid."""
    _fresh_db(monkeypatch, tmp_path)
    from engine.studio import render

    monkeypatch.delenv("AICMO_RENDER", raising=False)
    monkeypatch.setattr(render, "RENDERS_DIR", str(tmp_path / "renders"))

    called = {"placid": False}

    class _FakeClient:
        def is_configured(self):
            called["placid"] = True
            return True

    monkeypatch.setattr(render, "_placid_client", lambda: _FakeClient())

    pid = _drafted_post()
    render.run(pid)

    assert called["placid"] is False, "default path must not touch Placid"
    row = db_module.get_post(pid)
    assert row["image_path"], "image_path not set on default offline path"


def test_placid_path_taken_with_env_and_configured_client(monkeypatch, tmp_path):
    """With AICMO_RENDER=placid and a configured client, the Placid path runs."""
    _fresh_db(monkeypatch, tmp_path)
    from engine.studio import render

    monkeypatch.setenv("AICMO_RENDER", "placid")
    monkeypatch.setattr(render, "RENDERS_DIR", str(tmp_path / "renders"))

    calls = {"render_called": False}

    class _FakeClient:
        def is_configured(self):
            return True

        def default_template_uuid(self):
            return "tpl-uuid"

        def render_image(self, template_uuid, layers):
            calls["render_called"] = True
            calls["template_uuid"] = template_uuid
            calls["layers"] = layers
            return {"status": "finished", "image_url": "https://placid.test/out.png"}

    # The image fetch is local to render; stub it so no network is used.
    monkeypatch.setattr(render, "_placid_client", lambda: _FakeClient())
    monkeypatch.setattr(
        render, "_download_to", lambda url, path: _write_min_png(path)
    )

    pid = _drafted_post()
    render.run(pid)

    assert calls["render_called"] is True, "Placid render_image was not called"
    row = db_module.get_post(pid)
    assert row["image_path"], "image_path not set on Placid path"


def test_placid_falls_back_to_offline_on_error(monkeypatch, tmp_path):
    """If the Placid path raises, render still produces an offline image."""
    _fresh_db(monkeypatch, tmp_path)
    from engine.studio import render

    monkeypatch.setenv("AICMO_RENDER", "placid")
    monkeypatch.setattr(render, "RENDERS_DIR", str(tmp_path / "renders"))

    class _BoomClient:
        def is_configured(self):
            return True

        def default_template_uuid(self):
            return "tpl-uuid"

        def render_image(self, template_uuid, layers):
            raise RuntimeError("placid boom")

    monkeypatch.setattr(render, "_placid_client", lambda: _BoomClient())

    pid = _drafted_post()
    render.run(pid)

    row = db_module.get_post(pid)
    assert row["image_path"], "fallback image_path not set after Placid error"
    import os

    assert os.path.exists(row["image_path"]), "fallback PNG not written"


def _write_min_png(path):
    """Write a valid 1x1 PNG so the Placid test path produces a real file."""
    import struct
    import zlib

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(
            ">I", zlib.crc32(body) & 0xFFFFFFFF
        )

    raw = bytes([0]) + bytes([0xF7, 0xF3, 0xEC])
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)
