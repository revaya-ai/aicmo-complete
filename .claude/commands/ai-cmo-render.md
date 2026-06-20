---
description: STUDIO station. Take a drafted post, render it to an on-brand image, then brand-QC the image. On a pass it reaches qc_review. On a fail it regenerates the image and re-scores, up to two tries.
---

# /ai-cmo-render

Take a `drafted` post and walk it to `qc_review` with a real score and a rendered image. This is the Studio station: design the image, then check the design before any human sees it.

**Argument:** the post id of a `drafted` record. Example: `/ai-cmo-render 09c04e88242e411b8000ca531903ef17`

**Client:** `lumen-skin`.

## What to do

1. **Load the craft.** Read and follow `brand-test` (the scoring rubric). Read the client visual spec it points to:
   - `client-data/lumen-skin/visual-brand.md`
   - `client-data/lumen-skin/brand.css`

2. **Confirm the post is ready.** The record must be at status `drafted` with a hook and body. If not, stop and report the current status.

3. **Render the image.** Run from the repo root:

```bash
python3 -c "from engine.studio import render; render.run('<post_id>')"
```

This fills `templates/social/post.html.j2` with the hook and body and writes a real PNG to `renders/<post_id>.png` at 1080x1350. The default path needs no Playwright. To use the real browser render, set `AICMO_RENDER=playwright` first.

4. **Score the image.** Run:

```bash
python3 -c "from engine.studio import brand_qc; brand_qc.run('<post_id>')"
```

This scores the render against `brand-test`, gates at 85, and advances to `qc_review` on a pass or `needs_revision` on a fail.

5. **Handle a fail.** If the record landed at `needs_revision`, regenerate the IMAGE only, not the copy. Adjust the render, re-run render then brand_qc. Try at most twice. If it still fails, report the score and the failing dimensions and stop.

6. **Report back** the final status, the qc_score, the qc_notes, and the path to the rendered image.

## Rules

- Write ONLY these fields: image_path (render), qc_score, qc_notes (brand_qc). Status moves to qc_review or needs_revision automatically.
- On a fail, regenerate the image, never the words. Copy is locked once drafted.
- Do not modify `db.py` or any other station's files.
- No em dashes or hyphens as breaks. No emojis.
