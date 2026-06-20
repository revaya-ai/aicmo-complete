# Runs-For-Anyone Audit

**Auditor:** runs-for-anyone-auditor (independent QA, did not build this code)
**Date:** 2026-06-20
**Repo:** /Users/short/Downloads/aicmo-complete
**Python:** 3.14.3
**Charter:** Prove a stranger can clone this repo and get a working AI CMO offline, with no inside knowledge, and that nothing fails silently.

---

## TOP-LINE VERDICT: FAIL

The loop runs offline from the README with zero setup and reaches `ad_live`. The
tests are green. Reports and the Notion mirror produce real files. But the audit
fails on the No Silence rule: the headline artifact of the whole product, the
rendered post PNG, is a **blank off-white image with no text on it**, and the QC
gate **passes it at 90 with notes that describe text and a terracotta accent that
are not in the image**. A stranger following the README has no way to know the
"render" they just produced is empty, because every status, score, and note
reports success. That is exactly the failure mode the reference architecture
("watch for silence") exists to catch.

This is recoverable and the code is honest in its docstrings, but the README
sells a rendered, on-brand graphic and the default path does not deliver one.

---

## 1. README gaps (numbered, with the exact fix)

1. **The default render is a blank placeholder, and the README does not say so.**
   The README ("How to run the full loop") states: "A real PNG render lands in
   `renders/<post_id>.png` at 1080x1350." It is a real PNG at the right
   dimensions, but it is a **solid off-white rectangle with no hook, body, or
   accent** (`engine/studio/render.py` `_placeholder_png` paints one flat color;
   text only appears in the sibling `.html`, never composited into the PNG).
   **Fix:** State plainly that the default offline render is a blank brand-color
   placeholder carrying no text, that the text lives in `renders/<id>.html`, and
   that a real image (text composited) requires `AICMO_RENDER=playwright` plus
   `playwright install chromium`. Better: have the stdlib path draw the hook/body
   onto the PNG (e.g. via Pillow) so the default artifact is real.

2. **The QC pass is misleading and the README presents QC as a real gate.**
   The README and architecture describe a vision QC gate that "scores every
   render against the brand spec" with an 85 pass line. The default
   `engine/studio/brand_qc.py` only checks that the file exists and is non-zero
   bytes, then returns a hard-coded score of 90 with notes claiming a "legible
   serif headline" and "terracotta accent." Those are absent from the blank PNG.
   **Fix:** README should state that the default QC is a structural file check
   only (existence + non-empty), that the 90 score and brand notes are canned
   placeholders, and that real pixel-level brand scoring requires
   `AICMO_VISION_QC=claude`. The canned notes should not assert visual facts the
   default cannot verify.

3. **The README run command and the published_url stub are not flagged as fake.**
   The run prints `[publish] stub posted to linkedin: https://zernio.test/p/...`
   and stores that as `published_url`. It is clearly a `.test` host, which is
   fine, but the README never tells a new user the URL is a non-resolving stub.
   **Fix:** One line under "How to run the full loop": "The published URL is a
   stub (`zernio.test`); real publishing needs `ZERNIO_API_KEY`."

4. **Env var names disagree between the README and `.env.example`.**
   README "Going real" lists `META_ACCESS_TOKEN`, `LINKEDIN_ACCESS_TOKEN`,
   `DATAFORSEO_LOGIN`, `GSC_CREDENTIALS`, `APIFY_TOKEN`, `AICMO_RENDER`,
   `AICMO_VISION_QC`, `NOTION_TOKEN`. `.env.example` lists `ANTHROPIC_API_KEY`,
   `ZERNIO_API_KEY`, `META_ADS_TOKEN`, `LINKEDIN_ADS_TOKEN`, `NOTION_TOKEN` only.
   The Meta/LinkedIn names differ; `AICMO_RENDER`, `AICMO_VISION_QC`,
   `ANTHROPIC_API_KEY`, and the SEO keys are split across the two files.
   **Fix:** Make `.env.example` the single source of truth and align the README
   table to the exact same variable names. (Offline run is unaffected.)

5. **The README "commands" table is not runnable as written.**
   The `/ai-cmo-*` entries are Claude Code skills/commands, not shell commands. A
   brand-new user at a terminal cannot run `/ai-cmo-report`. The runnable
   equivalent is `python3 -m engine.dashboard.report`.
   **Fix:** Note that `/ai-cmo-*` are Claude Code commands, and give the plain
   `python3 -m engine.dashboard.report` / `engine.dashboard.notion_mirror`
   invocations for users without Claude Code.

---

## 2. Run result + artifact check

**Command:** `rm -f data/aicmo.db && python3 run.py "why competitors all sound the same"`
**Final status reached:** `ad_live` (full pipeline completed unattended).
Every transition printed; final row printed as JSON. Exit clean.

Pipeline observed: captured -> drafted -> qc_review -> approved -> scheduled ->
published -> analyzed -> ad_live (engagement 0.071 cleared the 0.03 promote
threshold, so it went the winner path through ads).

### Artifact check table

| Artifact | Path | Exists | Non-empty | Real / valid |
|---|---|---|---|---|
| Post render PNG | `renders/<id>.png` | YES | YES (6217 B) | Valid PNG 1080x1350, **but BLANK — no text, no accent** |
| Post render HTML | `renders/<id>.html` | YES | YES (1524 B) | Real, contains hook + body |
| Ad creative PNG | `renders/<id>-ad.png` | YES | YES (4978 B) | Valid PNG 1080x1080, **also blank** |
| DB record row | `data/aicmo.db` posts table | YES | YES | 1 row, status `ad_live`, all fields populated, queried via `db.DB_PATH` |
| `published_url` in row | (DB field) | YES | YES | `https://zernio.test/p/...` — stub host, non-resolving (by design) |
| `metrics_json` in row | (DB field) | YES | YES | `{likes:105, comments:13, shares:17, follows:18, impressions:2140}` |
| Weekly brief | `outputs/reports/weekly-brief-2026-06-20.md` | YES | YES (398 B) | Real, content matches pipeline state |
| Notion mirror | `outputs/notion-mirror.json` | YES (after running module) | YES (696 B) | Real JSON board; NOT written by the main loop, only by the mirror/report command |

DB query method: `sqlite3.connect(db.DB_PATH)` against the module's own
`DB_PATH`. `import db` has no side effects (confirmed by reading `db.py` and
`run.py`); a one-row deterministic record results from each clean run.

---

## 3. Silent successes (success reported, artifact empty or unverifiable)

1. **Render reports a render; the PNG carries no content.** `studio.render`
   advances the post and writes a valid PNG, but the default stdlib path paints a
   single flat color. Opening `renders/<id>.png` shows a blank off-white canvas.
   The product's central output (an on-brand graphic) is not produced on the
   default path. Reference architecture E ("all copy lands through the template")
   is not satisfied by the default artifact.

2. **QC reports "on brand, score 90" on a blank image.** `studio.brand_qc`
   `_detect_off_brand` only checks file existence and non-zero size; it never
   inspects pixels. `score_image(False)` returns a hard-coded 90 with notes
   asserting a "legible serif headline" and "terracotta accent" that do not exist
   in the blank PNG. The gate that is supposed to stop off-brand output from
   reaching the human passes an empty image and fabricates the reason.

3. **Notion mirror is not produced by the end-to-end loop.** The README implies
   the loop and `/ai-cmo-report` mirror to Notion. `run.py` does not write
   `outputs/notion-mirror.json`; it only appears after running the mirror module
   directly. Low severity (it is a stub and gitignored), but the loop does not
   produce it despite the architecture listing it under dashboard/reporting.

All three are documented as stubs in the relevant docstrings, so they are
not crashes. They are silent successes because the user-facing surface (status,
score, brand notes) claims a real, on-brand result while the artifact is empty.

---

## 4. Test result

`python3 -m pytest -q` -> **47 passed, 0 failed, 0 skipped** in 0.38s.
Only warnings: repeated `datetime.utcnow()` DeprecationWarning (85 warnings) in
`db.py`, `report.py`, `feedback.py`, `schedule.py`. Non-blocking on 3.14 but
should be migrated to `datetime.now(datetime.UTC)` before a future Python drops
`utcnow()`.

Note: tests pass because they assert the contract and status transitions, and
`brand_qc` is tested via the **pure** `score_image(off_brand)` function. No test
asserts that the rendered PNG actually contains the hook/body text, which is why
the blank-render silent success slips through green tests.

---

## 5. Non-loop command check

Ran `python3 -m engine.dashboard.report` (the runnable equivalent of the
README's `/ai-cmo-report`). It wrote `outputs/reports/weekly-brief-2026-06-20.md`
(398 B), a real weekly brief that correctly reports 1 post in the pipeline at
`ad_live`, an estimated run cost, the winning post by engagement rate, and a next
move. Also ran `python3 -m engine.dashboard.notion_mirror`, which wrote a real
696 B `outputs/notion-mirror.json` board. Both do what the README describes.

---

## 6. What a stranger gets, in one paragraph

Clone, `python3 run.py "<idea>"`, no installs, no keys: the loop runs green to
`ad_live`, the DB row is real and complete, the reports are real. That is a
genuine, auditable, offline end-to-end pipeline and it is close. But the two
artifacts a content marketing tool exists to produce, the rendered post image and
a trustworthy QC verdict, are hollow on the default path: a blank PNG passed off
as on-brand at 90. Fix the render to composite text (or document the placeholder
loudly) and make the QC verdict honest about what it actually checked, and this
moves to PASS.

---

## Single most important fix

Make the default offline render composite the hook and body text onto the PNG
(stdlib bitmap font or Pillow), and have `brand_qc` either inspect the pixels or
return notes that only claim what the structural check actually verified. Until
the default PNG carries the post's words, the system's headline artifact is a
silent success.
