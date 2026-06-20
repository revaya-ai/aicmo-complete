---
name: brand-test
description: The rubric a vision model scores a rendered post against. A 0 to 100 scale with a hard 85 pass line. Loaded by the ai-cmo-render command and used by engine/studio/brand_qc.py. The craft of judging whether an image is on brand before a human ever sees it.
---

# brand-test

## Purpose

Before a human reviews a post, the Studio renders an image and scores it against the client's visual brand. This skill is the rubric. It turns "does this look on brand" into a number so the gate is consistent, not a vibe.

## Before you score

Read the client's visual spec first:
- `client-data/<client>/visual-brand.md` for colors, fonts, the layout feel, and the visual "never" list.
- `client-data/<client>/brand.css` for the exact color and font values the renderer used.

Score the image against THAT spec, not against general taste.

## The scale

A 0 to 100 score. The pass line is 85. A score of 85 or higher advances to qc_review for the human gate. Below 85 routes to needs_revision and the image is regenerated, not the copy.

## The five scoring dimensions

Each dimension is worth 20 points. Add them for the final score.

### 1. On-brand color (20)
The background, accent, and ink match the spec within a small tolerance. No off-palette color. No neon, no high saturation. Grey is never a primary color.
- 20: every color is on palette.
- 10: one minor off-palette element.
- 0: a dominant off-palette or banned color.

### 2. Typography (20)
Headline uses the spec serif, body uses the spec sans. No more than two fonts. Headline is the focal line.
- 20: correct fonts, clear hierarchy.
- 10: right fonts, weak hierarchy.
- 0: wrong fonts or three or more fonts.

### 3. Layout and whitespace (20)
Calm, airy, editorial. Generous padding. One focal line. Not crowded. White space is the brand.
- 20: breathing room, clear focal point.
- 10: a little tight.
- 0: crowded or cluttered.

### 4. Legibility and contrast (20)
The hook and body are easy to read at a glance. Text sits cleanly on the background with enough contrast. No text running off the canvas.
- 20: effortless to read.
- 10: readable but low contrast in places.
- 0: hard to read or clipped text.

### 5. No banned visual patterns (20)
None of the visual "never" list appears: no stock "perfect skin" close-ups, no clip-art icons, no emoji-heavy graphics, no model-generated text baked into the image.
- 20: clean, none present.
- 10: one borderline element.
- 0: a clear banned pattern.

## How to apply it (offline default)

The default offline check in `engine/studio/brand_qc.py` does not call a vision model. It treats a clean render as a 90 and a flagged render as a 60, so the 85 line still gates correctly and the loop runs with no API key. When `AICMO_VISION_QC=claude` is set, send the image plus this rubric and `visual-brand.md` to a Claude vision call and return the summed score with one note per dimension that lost points.

## Worth scoring two images differently

A render on the warm off-white background with a terracotta rule and a single serif headline scores near 95. A render with a neon background, three fonts, and a stock face scores near 35. The rubric separates them. That separation is the whole point.

## Output contract

Return exactly two things to brand_qc.py:
- an integer score, 0 to 100.
- short notes, one line per dimension that lost points. If nothing lost points, say so in one line.
