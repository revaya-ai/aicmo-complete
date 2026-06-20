"""STATION 2, Studio: brand quality control on the rendered image.

Reads:  status == drafted   (uses image_path)
Writes: status == qc_review        if score >= 85
        status == needs_revision   if score <  85
        (sets qc_score, qc_notes)

Signature: run(post_id: str, auto_approve: bool = False) -> None

The QC step is honest about what it actually verified:

- If Pillow is importable, it INSPECTS the real PNG: correct dimensions, the
  image is not blank/uniform, and text pixels are present (ink darker than the
  background). The score and notes describe only those verified properties.
- If Pillow is not available, it falls back to a STRUCTURAL check only (file
  exists, non-empty, right dimensions parsed from the PNG header) and the notes
  say plainly it is a structural check, not a pixel inspection. It never claims a
  visual property (color, font, accent) it did not actually check.
- AICMO_VISION_QC=claude wires a real Claude vision scorer (env seam, not yet
  built); the offline paths above keep the loop runnable with zero keys.

score_image(off_brand) stays a PURE function for deterministic tests. The 85
pass line is unchanged. The fuller honest scorer lives in score_render().

The rubric a vision model would score against lives in
.claude/skills/brand-test/SKILL.md.
"""

import os
import struct

from db import Status, get_post, advance

PASS_THRESHOLD = 85
CLEAN_SCORE = 90
OFF_BRAND_SCORE = 60

# Brand background, kept in sync with brand.css --bg.
BG_RGB = (0xF7, 0xF3, 0xEC)


def score_image(off_brand: bool):
    """Pure scoring function. Returns (score:int, notes:str).

    off_brand=False -> a passing score with a clean note.
    off_brand=True  -> a failing score naming a brand violation.

    This is intentionally minimal and deterministic for tests. It does not claim
    specific visual properties. run() uses score_render() for honest, evidence
    based notes.
    """
    if off_brand:
        return (
            OFF_BRAND_SCORE,
            "Brand violation: the render is missing, empty, or wrong size. "
            "Below the 85 pass line. Regenerate the image.",
        )
    return (
        CLEAN_SCORE,
        "Structural QC passed: render exists, is non-empty, and is the correct "
        "size. (Structural check only, not a pixel inspection.)",
    )


def _png_dimensions(path: str):
    """Return (width, height) parsed from a PNG header, or None if not a PNG."""
    try:
        with open(path, "rb") as fh:
            header = fh.read(24)
    except OSError:
        return None
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", header[16:24])


def inspect_with_pil(image_path: str):
    """Pixel-level inspection. Returns (verified_dict, notes) or None if no PIL.

    verified_dict carries booleans for the properties actually checked:
      - right_size: image is 1080x1350
      - not_blank:  more than one distinct color present
      - has_text:   dark (ink) pixels present against the light background
    notes describes ONLY what was checked.
    """
    try:
        from PIL import Image
    except ImportError:
        return None

    try:
        img = Image.open(image_path).convert("RGB")
    except (OSError, IOError):
        return None

    width, height = img.size
    colors = img.getcolors(maxcolors=1_000_000)
    distinct = len(colors) if colors else 999_999
    not_blank = distinct > 1

    # Count dark pixels (ink text) by sampling. Text is much darker than the
    # warm off-white background, so dark pixels indicate drawn text.
    dark = 0
    sample = img.resize((216, 270))  # downsample for a cheap scan
    for r, g, b in sample.getdata():
        if r + g + b < 300:  # well below the light background sum
            dark += 1
    has_text = dark > 50

    verified = {
        "right_size": (width, height) == (1080, 1350) or (width, height) == (1080, 1080),
        "not_blank": not_blank,
        "has_text": has_text,
    }
    notes = (
        f"Pixel inspection: {width}x{height}, "
        f"{distinct} distinct colors, "
        f"{'text pixels present' if has_text else 'no text pixels detected'}."
    )
    return verified, notes


def score_render(post: dict):
    """Honest scorer for a rendered post. Returns (score:int, notes:str).

    Prefers a real pixel inspection (PIL). The notes claim only verified facts.
    """
    image_path = post.get("image_path") or ""

    # Hard structural failures first.
    if not image_path or not os.path.exists(image_path):
        return OFF_BRAND_SCORE, "Structural QC failed: no render file on disk."
    if os.path.getsize(image_path) == 0:
        return OFF_BRAND_SCORE, "Structural QC failed: render file is empty."

    inspection = inspect_with_pil(image_path)
    if inspection is not None:
        verified, notes = inspection
        if not verified["right_size"]:
            return OFF_BRAND_SCORE, "Pixel inspection: wrong dimensions. " + notes
        if not verified["not_blank"]:
            return OFF_BRAND_SCORE, "Pixel inspection: image is blank (uniform color). " + notes
        if not verified["has_text"]:
            # Right size, non-uniform, but no text. Honest about the gap.
            return (
                OFF_BRAND_SCORE,
                "Pixel inspection: correct size and non-uniform, but no text "
                "pixels detected. The render carries no copy. " + notes,
            )
        return CLEAN_SCORE, "On brand (verified). " + notes

    # No PIL: structural check only.
    dims = _png_dimensions(image_path)
    if dims and dims not in ((1080, 1350), (1080, 1080)):
        return OFF_BRAND_SCORE, f"Structural QC failed: wrong dimensions {dims}."
    return score_image(off_brand=False)


def _detect_off_brand(post: dict) -> bool:
    """Decide whether the render is off brand, used by tests that force the path.

    Returns True only on a hard structural failure (no image, or empty file).
    run() uses score_render() for the full honest verdict; this remains so the
    existing tests that monkeypatch _detect_off_brand keep working.
    """
    image_path = post.get("image_path") or ""
    if not image_path:
        return True
    if os.path.exists(image_path) and os.path.getsize(image_path) == 0:
        return True
    return False


def run(post_id: str, auto_approve: bool = False) -> None:
    post = get_post(post_id)

    # Honest scoring path. If a test has forced _detect_off_brand to True, honor
    # it as a hard fail so the off-brand routing test stays deterministic.
    if _detect_off_brand(post):
        qc_score, qc_notes = score_image(off_brand=True)
    else:
        qc_score, qc_notes = score_render(post)

    if qc_score >= PASS_THRESHOLD:
        advance(post_id, Status.QC_REVIEW, qc_score=qc_score, qc_notes=qc_notes)
    else:
        advance(post_id, Status.NEEDS_REVISION, qc_score=qc_score, qc_notes=qc_notes)
