"""STATION 2 — Studio: draft -> rendered image.

Reads:  status == drafted   (uses hook, body)
Writes: image_path          (status stays drafted; brand_qc moves it next)

Signature: run(post_id: str, auto_approve: bool = False) -> None

Two render paths:

1. DEFAULT (stdlib only, no dependencies): fill the HTML template with the
   post's hook and body, then write a deterministic placeholder PNG at exactly
   1080x1350 to renders/<post_id>.png. The placeholder is a real, valid PNG file
   painted in the brand background color so the whole loop runs offline.

2. REAL (opt in with AICMO_RENDER=playwright): screenshot the filled template
   with Playwright at 1080x1350 @2x. Only taken when the env var is set AND
   playwright is importable, so the default path never requires it.

The HTML is always written next to the PNG (renders/<post_id>.html) so a human
can open the real layout in a browser.
"""

import os
import re
import struct
import zlib

from db import get_post, update_post

# Brand spec, kept in sync with client-data/lumen-skin/visual-brand.md.
WIDTH = 1080
HEIGHT = 1350
BG_RGB = (0xF7, 0xF3, 0xEC)  # warm off-white --bg

RENDERS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "renders")
TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "templates", "social", "post.html.j2"
)


def fill_template(hook: str, body: str) -> str:
    """Substitute {{ hook }} and {{ body }} into the post template.

    Uses a tiny stdlib substitution so render works without Jinja2. If Jinja2 is
    installed it is used for parity with the production renderer.
    """
    with open(TEMPLATE_PATH, encoding="utf-8") as fh:
        template = fh.read()
    try:
        from jinja2 import Template

        return Template(template).render(hook=hook, body=body)
    except ImportError:
        html = re.sub(r"\{\{\s*hook\s*\}\}", hook, template)
        html = re.sub(r"\{\{\s*body\s*\}\}", body, html)
        return html


def _placeholder_png(path: str, width: int, height: int, rgb) -> None:
    """Write a real, valid PNG of solid color using stdlib only.

    Deterministic: the same dimensions and color always produce the same bytes.
    """

    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    r, g, b = rgb
    # One scanline: filter byte 0 then width pixels of RGB.
    row = bytes([0]) + bytes([r, g, b]) * width
    raw = row * height
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8-bit RGB
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


def _render_with_playwright(html: str, image_path: str) -> bool:
    """Real render path. Returns True on success, False if unavailable."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=2
        )
        page.set_content(html, wait_until="networkidle")
        page.screenshot(path=image_path, clip={"x": 0, "y": 0, "width": WIDTH, "height": HEIGHT})
        browser.close()
    return True


def run(post_id: str, auto_approve: bool = False) -> None:
    post = get_post(post_id)
    os.makedirs(RENDERS_DIR, exist_ok=True)
    image_path = os.path.join(RENDERS_DIR, f"{post_id}.png")
    html_path = os.path.join(RENDERS_DIR, f"{post_id}.html")

    html = fill_template(post["hook"], post["body"])
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(html)

    used_real = False
    if os.environ.get("AICMO_RENDER") == "playwright":
        used_real = _render_with_playwright(html, image_path)
    if not used_real:
        _placeholder_png(image_path, WIDTH, HEIGHT, BG_RGB)

    # Store a repo-relative path so the Flask gate can serve it directly. If the
    # render dir lives outside the repo (e.g. a test tmp dir), keep it absolute.
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    abs_image = os.path.abspath(image_path)
    if abs_image.startswith(repo_root + os.sep):
        stored = os.path.relpath(abs_image, repo_root)
    else:
        stored = abs_image
    update_post(post_id, image_path=stored)
