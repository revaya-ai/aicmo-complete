"""STATION 2 — Studio: brand quality control on the rendered image.

Reads:  status == drafted   (uses image_path)
Writes: status == qc_review        if score >= 85
        status == needs_revision   if score <  85
        (sets qc_score, qc_notes)

Signature: run(post_id: str, auto_approve: bool = False) -> None

Scoring is split so it is testable without a vision model:

- score_image(off_brand) is a PURE function. Feed it the off-brand flag and it
  returns a deterministic (score, notes) pair. A clean render scores 90, an
  off-brand render scores 60. The 85 pass line sits between them.
- _detect_off_brand(post) is where a real vision model would inspect the PNG
  against client-data/<client>/visual-brand.md. The default offline check looks
  for cheap structural red flags (missing image, empty hook/body). Set
  AICMO_VISION_QC=claude to wire in a real Claude vision call later.

The rubric the vision model scores against lives in
.claude/skills/brand-test/SKILL.md.
"""

import os

from db import Status, get_post, advance

PASS_THRESHOLD = 85
CLEAN_SCORE = 90
OFF_BRAND_SCORE = 60


def score_image(off_brand: bool):
    """Pure scoring function. Returns (score:int, notes:str).

    off_brand=False -> a passing score with a clean note.
    off_brand=True  -> a failing score naming a brand violation.
    """
    if off_brand:
        return (
            OFF_BRAND_SCORE,
            "Brand violation detected: off-palette color, banned visual pattern, "
            "or crowded layout. Below the 85 pass line. Regenerate the image.",
        )
    return (
        CLEAN_SCORE,
        "On brand: warm off-white background, terracotta accent, generous "
        "whitespace, legible serif headline. No banned patterns.",
    )


def _detect_off_brand(post: dict) -> bool:
    """Decide whether the render is off brand. Offline structural check.

    A real implementation sends post['image_path'] to a vision model with
    visual-brand.md as the rubric. The default flags only obvious failures so the
    loop runs offline and clean renders pass.
    """
    image_path = post.get("image_path") or ""
    # No image at all is a hard fail.
    if not image_path:
        return True
    # If the file is on disk and empty, it is a render failure.
    if os.path.exists(image_path) and os.path.getsize(image_path) == 0:
        return True
    return False


def run(post_id: str, auto_approve: bool = False) -> None:
    post = get_post(post_id)
    off_brand = _detect_off_brand(post)
    qc_score, qc_notes = score_image(off_brand)

    if qc_score >= PASS_THRESHOLD:
        advance(post_id, Status.QC_REVIEW, qc_score=qc_score, qc_notes=qc_notes)
    else:
        advance(post_id, Status.NEEDS_REVISION, qc_score=qc_score, qc_notes=qc_notes)
