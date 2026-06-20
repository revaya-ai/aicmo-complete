"""STATION 2 — Studio: brand quality control on the rendered image.

Reads:  status == drafted   (uses image_path)
Writes: status == qc_review        if score >= 85
        status == needs_revision   if score <  85
        (sets qc_score, qc_notes)

Signature: run(post_id: str, auto_approve: bool = False) -> None

The real version sends image_path to a vision model and scores it against
visual-brand.md (colors, fonts, the "never" list). A score >= 85 passes to
qc_review for the human gate. The stub returns 90 so the loop always passes.
"""

from db import Status, get_post, advance

PASS_THRESHOLD = 85


def run(post_id: str, auto_approve: bool = False) -> None:
    post = get_post(post_id)

    # TODO(builder): load the image at post["image_path"], send it to a vision
    # model with visual-brand.md as the rubric, and return an integer 0-100
    # plus short notes on any brand violations.
    qc_score = 90
    qc_notes = "STUB: vision QC not run. Assumed on-brand."

    if qc_score >= PASS_THRESHOLD:
        advance(post_id, Status.QC_REVIEW, qc_score=qc_score, qc_notes=qc_notes)
    else:
        advance(post_id, Status.NEEDS_REVISION, qc_score=qc_score, qc_notes=qc_notes)
