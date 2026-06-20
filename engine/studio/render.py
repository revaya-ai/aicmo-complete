"""STATION 2, Studio: draft to rendered image.

Reads:  status == drafted   (uses hook, body)
Writes: image_path          (status stays drafted; brand_qc moves it next)

Signature: run(post_id: str, auto_approve: bool = False) -> None

Three render paths, in order of preference:

1. PREFERRED DEFAULT (Pillow, if importable): draw the hook and body text onto
   the 1080x1350 canvas in the brand colors from brand.css, so the default PNG
   actually contains the post's words. No browser needed.

2. STDLIB FALLBACK (no Pillow): write a deterministic solid brand-color PNG at
   1080x1350 using the stdlib only. This carries no text, so the QC step is
   honest that it is a structural check, not a pixel inspection.

3. REAL PLACID (opt in with AICMO_RENDER=placid): composite the post onto an
   on-brand Placid template and save the returned image. Only taken when the env
   var is set AND the Placid client is configured (PLACID_API_TOKEN present). On
   any error it falls back to the offline render so the loop never breaks.

4. REAL PLAYWRIGHT (opt in with AICMO_RENDER=playwright): screenshot the filled
   template with Playwright at 1080x1350 @2x. Only taken when the env var is set
   AND playwright is importable.

Selection order: placid (if configured) -> playwright -> PIL default -> stdlib
fallback. With no AICMO_RENDER env var the default path stays exactly as before:
PIL when importable, stdlib placeholder otherwise. Offline, no token, no network.

The HTML is always written next to the PNG (renders/<post_id>.html) so a human
can open the real layout in a browser.
"""

import os
import re
import struct
import urllib.request
import zlib

from db import get_post, update_post

# Brand spec, kept in sync with client-data/lumen-skin/visual-brand.md and
# client-data/lumen-skin/brand.css.
WIDTH = 1080
HEIGHT = 1350
BG_RGB = (0xF7, 0xF3, 0xEC)  # warm off-white --bg
INK_RGB = (0x2E, 0x26, 0x20)  # deep brown --ink
ACCENT_RGB = (0xC7, 0x7B, 0x58)  # soft terracotta --accent
PAD = 96  # generous whitespace --pad

# Ad creative dimensions (brick B4.2). Square 1080x1080 is the safe default for
# Meta and LinkedIn feed ads, distinct from the 1080x1350 organic post.
AD_WIDTH = 1080
AD_HEIGHT = 1080

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


def _render_with_pil(hook: str, body: str, image_path: str, width: int, height: int) -> bool:
    """Preferred default render: draw the hook and body onto the canvas with PIL.

    Returns True if Pillow is available and the image was drawn, False otherwise
    so the caller can fall back to the stdlib placeholder. Uses the brand colors
    (background, ink, terracotta accent rule) so the PNG is on brand AND carries
    the post's actual words.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return False

    img = Image.new("RGB", (width, height), BG_RGB)
    draw = ImageDraw.Draw(img)

    # Try a real TrueType font from common locations; fall back to a sized
    # default font so text is always drawn at a legible size.
    def _load_font(size):
        candidates = (
            "DejaVuSerif.ttf",
            "DejaVuSans.ttf",
            "/System/Library/Fonts/Supplemental/Georgia.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        )
        for name in candidates:
            try:
                return ImageFont.truetype(name, size)
            except (OSError, IOError):
                continue
        try:
            return ImageFont.load_default(size)
        except TypeError:
            return ImageFont.load_default()

    hook_font = _load_font(72)
    body_font = _load_font(34)

    text_width = width - 2 * PAD

    def _wrap(text, font):
        lines = []
        for paragraph in text.split("\n"):
            if not paragraph.strip():
                lines.append("")
                continue
            words = paragraph.split()
            current = ""
            for word in words:
                trial = (current + " " + word).strip()
                if draw.textlength(trial, font=font) <= text_width:
                    current = trial
                else:
                    if current:
                        lines.append(current)
                    current = word
            if current:
                lines.append(current)
        return lines

    y = PAD
    # Hook (serif, ink).
    for line in _wrap(hook, hook_font):
        draw.text((PAD, y), line, fill=INK_RGB, font=hook_font)
        bbox = draw.textbbox((0, 0), line or "Ag", font=hook_font)
        y += int((bbox[3] - bbox[1]) * 1.3) + 8

    # Terracotta accent rule.
    y += 24
    draw.rectangle([PAD, y, PAD + 120, y + 6], fill=ACCENT_RGB)
    y += 48

    # Body (sans, ink).
    for line in _wrap(body, body_font):
        draw.text((PAD, y), line, fill=INK_RGB, font=body_font)
        bbox = draw.textbbox((0, 0), line or "Ag", font=body_font)
        y += int((bbox[3] - bbox[1]) * 1.5) + 6

    img.save(image_path, "PNG")
    return True


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


def _placid_client():
    """Build a Placid client. Indirected so tests can inject a fake."""
    from engine.integrations.placid import PlacidClient

    return PlacidClient()


def _download_to(url: str, path: str) -> None:
    """Download a finished Placid image URL to a local path. Stdlib only.

    Only ever called on the Placid path, which is itself gated on AICMO_RENDER
    AND a configured client, so the default offline path never reaches here.
    """
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    with open(path, "wb") as fh:
        fh.write(data)


def _render_with_placid(hook: str, body: str, image_path: str) -> bool:
    """Optional backend: composite the post onto an on-brand Placid template.

    Maps the hook, body, and brand background color to named template layers,
    starts the render, and saves the returned image to image_path. Returns True
    on success, False if Placid is not configured or anything fails, so the
    caller falls back to the offline render and the loop never breaks.
    """
    try:
        client = _placid_client()
    except Exception:
        return False
    if not client.is_configured():
        return False
    try:
        template_uuid = client.default_template_uuid()
        layers = {
            "hook": {"text": hook},
            "body": {"text": body},
            "background": {"color": "#F7F3EC"},
        }
        result = client.render_image(template_uuid, layers) or {}
        image_url = result.get("image_url")
        # Placid jobs may queue; poll once via get_image if a polling id is given.
        if not image_url and result.get("id"):
            polled = client.get_image(result["id"]) or {}
            image_url = polled.get("image_url")
        if not image_url:
            return False
        _download_to(image_url, image_path)
        return True
    except Exception:
        return False


def _gemini_client():
    """Build a Gemini image client. Indirected so tests can inject a fake."""
    from engine.integrations.gemini import GeminiImageClient

    return GeminiImageClient()


def _render_with_gemini(hook: str, body: str, image_path: str) -> bool:
    """Optional backend: generate an on-brand image with Gemini (Nano Banana).

    Builds a brand-appropriate prompt from the hook and body, calls the image
    model, and writes the returned bytes to image_path. Returns True on success,
    False if Gemini is not configured or anything fails, so the caller falls back
    to the offline render and the loop never breaks.
    """
    try:
        client = _gemini_client()
    except Exception:
        return False
    if not client.is_configured():
        return False
    try:
        prompt = (
            "Editorial skincare social image, calm and minimal. "
            "Warm off-white background (#F7F3EC), deep brown ink (#2E2620), "
            "a single soft terracotta accent (#C77B58). Clean negative space, "
            "premium quiet aesthetic. "
            f"Headline idea: {hook}. "
            f"Supporting message: {body}."
        )
        data = client.generate_image(prompt)
        if not data:
            return False
        with open(image_path, "wb") as fh:
            fh.write(data)
        return True
    except Exception:
        return False


def render_ad(post_id: str) -> str:
    """STUDIO contributes to ADS (brick B4.2): render an ad-sized creative.

    Reads:  the post's hook and body.
    Writes: an ad-sized placeholder PNG to renders/<post_id>-ad.png and returns
            its path. The caller (the ads flow) records the path on the row; this
            function does not advance any status.

    Default path is stdlib-only (a valid placeholder PNG at AD_WIDTH x AD_HEIGHT
    in the brand background color). The real Playwright path is taken only when
    AICMO_RENDER=playwright is set, mirroring run() so the loop stays offline.
    """
    post = get_post(post_id)
    os.makedirs(RENDERS_DIR, exist_ok=True)
    image_path = os.path.join(RENDERS_DIR, f"{post_id}-ad.png")
    html_path = os.path.join(RENDERS_DIR, f"{post_id}-ad.html")

    html = fill_template(post.get("hook") or "", post.get("body") or "")
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(html)

    hook = post.get("hook") or ""
    body = post.get("body") or ""

    backend = os.environ.get("AICMO_RENDER")
    drawn = False
    if backend == "placid":
        drawn = _render_with_placid(hook, body, image_path)
        if drawn:
            print("[render] ad backend: placid")
    elif backend == "gemini":
        drawn = _render_with_gemini(hook, body, image_path)
        if drawn:
            print("[render] ad backend: gemini")
    elif backend == "playwright":
        drawn = _render_ad_with_playwright(html, image_path)
        if drawn:
            print("[render] ad backend: playwright")
    if not drawn:
        drawn = _render_with_pil(hook, body, image_path, AD_WIDTH, AD_HEIGHT)
        if drawn:
            print("[render] ad backend: pil")
    if not drawn:
        _placeholder_png(image_path, AD_WIDTH, AD_HEIGHT, BG_RGB)
        print("[render] ad backend: stdlib")
    return image_path


def _render_ad_with_playwright(html: str, image_path: str) -> bool:
    """Real ad render path at ad dimensions. Returns True on success."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": AD_WIDTH, "height": AD_HEIGHT}, device_scale_factor=2
        )
        page.set_content(html, wait_until="networkidle")
        page.screenshot(
            path=image_path, clip={"x": 0, "y": 0, "width": AD_WIDTH, "height": AD_HEIGHT}
        )
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

    backend = os.environ.get("AICMO_RENDER")
    drawn = False
    if backend == "placid":
        drawn = _render_with_placid(post["hook"], post["body"], image_path)
        if drawn:
            print("[render] backend: placid")
    elif backend == "gemini":
        drawn = _render_with_gemini(post["hook"], post["body"], image_path)
        if drawn:
            print("[render] backend: gemini")
    elif backend == "playwright":
        drawn = _render_with_playwright(html, image_path)
        if drawn:
            print("[render] backend: playwright")
    if not drawn:
        drawn = _render_with_pil(post["hook"], post["body"], image_path, WIDTH, HEIGHT)
        if drawn:
            print("[render] backend: pil")
    if not drawn:
        _placeholder_png(image_path, WIDTH, HEIGHT, BG_RGB)
        print("[render] backend: stdlib")

    # Store a repo-relative path so the Flask gate can serve it directly. If the
    # render dir lives outside the repo (e.g. a test tmp dir), keep it absolute.
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    abs_image = os.path.abspath(image_path)
    if abs_image.startswith(repo_root + os.sep):
        stored = os.path.relpath(abs_image, repo_root)
    else:
        stored = abs_image
    update_post(post_id, image_path=stored)
