# Hackathon Assignments: AI CMO

Three builders. Four stations (the 4th, Ads, is split across all three). Build your piece on your own branch against the stub scaffold, then we merge at the end of the day.

---

## The rule that makes this work

`db.py` is the **frozen contract**. It already runs green end-to-end with stubs. You do NOT change it. You replace your station's stub with real logic, keep the same function signature (`def run(post_id, auto_approve=False)`), read your input status, write your output status. Because every station lives in its own folder, our branches merge with near-zero conflicts.

**Test your station in isolation any time:**
```bash
python3 run.py "any seed idea"     # runs the whole loop; your real station + everyone else's stubs
```
Your part is done when your transition is real and the loop is still green.

---

## Git workflow (build separately → combine at end)

```bash
git clone <repo-url> aicmo-core
cd aicmo-core
git checkout -b brain      # or: studio / mission   (your station name)
# ...build...
git add -A && git commit -m "brain: real Brick chain"
git push -u origin brain
```
At the integration window (~5:00pm) we merge all three branches into `main` and run the full loop live. Whoever owns Mission Control is the merge/integration captain.

---

# CARD 1: BRAIN  (Think + Write)

**Mission:** turn a seed idea into an on-brand draft.

**Files you own:**
- `engine/brain/generate.py`
- `client-data/lumen-skin/*.md` (the 6-layer context, you set the format everyone grounds against)

**Your contract:** read status `captured` → write status `drafted` (fill `pillar`, `angle`, `hook`, `body`).

**Build checklist:**
- [ ] Finish the 6-layer context for the demo client (positioning, brand & audience, strategy, offers, voice, guardrails). FIRST, Studio and the QC gate depend on it.
- [ ] Brick chain in `generate.py`: Intake → Topic (1 line + which pillar) → Angle → Hook → Story. Each step grounded in the markdown context. Use Claude (Anthropic SDK).
- [ ] Anti-AI-slop pass before the body is final (reuse the `humanizer` approach: banned patterns, no em dashes, no generic openers).
- [ ] Write the finished draft to the DB at `drafted`.

**Your Ads contribution:** add a function that produces ad-format copy variants from a winning post (Mission Control calls it during ads assembly).

**Definition of done:** `python3 run.py "..."` produces a `drafted` row whose body reads genuinely on-brand and passes a manual sniff test.

**Do NOT touch:** `db.py`, `engine/studio/`, `engine/mission/`, `engine/ads/`.

---

# CARD 2: STUDIO  (Design + Check itself)

**Mission:** render the on-brand graphic and gate it before a human ever sees it.

**Files you own:**
- `engine/studio/render.py`
- `engine/studio/brand_qc.py`
- `templates/social/post.html.j2`
- `client-data/lumen-skin/visual-brand.md` + `brand.css`

**Your contract:** read `drafted` → set `image_path`, then write `qc_review` (pass) or `needs_revision` (fail). The gate is `qc_score >= 85`.

**Build checklist:**
- [ ] Finalize `visual-brand.md` + `brand.css` (accent, bg, fonts, voice, the "never" list). Brand facts come from Brain's context; you own the spec format.
- [ ] `render.py`: fill the HTML template → Playwright screenshot → 1080×1350 @2x PNG. **No text is ever written by the image model. All copy lands through the template.**
- [ ] `brand_qc.py`: send the PNG to Claude vision, score 0 to 100 vs the brand spec, return score + notes. ≥85 → `qc_review`; below → `needs_revision`.
- [ ] Prove the gate rejects: feed it a deliberately off-brand image and confirm it scores low and routes to `needs_revision`.

**Your Ads contribution:** add an ad-creative render (reuse `render.py` at ad dimensions).

**Definition of done:** a `drafted` row comes back with a real branded PNG + a real numeric QC score, and the gate actually rejects an off-brand test image.

**Do NOT touch:** `db.py`, `engine/brain/`, `engine/mission/`, `engine/ads/`.

---

# CARD 3: MISSION CONTROL  (Gate + Ship + Measure + Ads spine)

**Mission:** the human gate, distribution, analytics, the ads agent, and final integration. You are the integration captain and custodian of `db.py`.

**Files you own:**
- `engine/mission/gate.py` (the human approve/reject board, Flask app already stubbed)
- `engine/mission/schedule.py`, `publish.py`, `analytics.py`
- `engine/ads/ads_agent.py`
- `run.py` orchestration + `README.md`
- `db.py` (custodian, but changes still require all three to agree)

**Your contract:** read `qc_review` → drive `approved → scheduled → published → analyzed`, then `ad_recommended → ad_approved → ad_live`.

**Build checklist:**
- [ ] Human gate: a real board listing `qc_review` rows (post + image) with Approve / Reject. Approve → `approved`; Reject → `needs_revision` + capture `human_note`. (Flask local page is fine; Notion mirror is the stretch.)
- [ ] `schedule.py`: pick a slot → `scheduled`.
- [ ] `publish.py`: **Zernio** publish (use the teammate's account). Floor = stub that logs + writes a fake `published_url` so the demo never depends on a live key.
- [ ] `analytics.py`: pull metrics back → `metrics_json` → `analyzed`. (Mock is acceptable; real Zernio analytics is stretch.)
- [ ] `ads_agent.py`: detect winners at `analyzed` → write an `ad_recommended` record (uses Brain's ad copy + Studio's ad creative) → **spend-approval gate** (reuse the gate UI) → `ad_approved` → push to Meta/LinkedIn Ads. **Floor = stub pusher behind the spend gate; real Ads API is stretch.** Ads API auth must never block the core content loop.
- [ ] Own the integration window + the live demo.

**Definition of done:** approve on the gate → the row walks to `published` → `analyzed` → ad recommendation → approve spend → `ad_live`.

**Do NOT touch:** `engine/brain/` internals, `engine/studio/` internals (you call them, you don't rewrite them).

---

## End-of-day combine (integration window)

1. Each builder pushes their branch.
2. Mission Control merges `brain`, `studio`, `mission` into `main` (folders are isolated → clean merges).
3. Run `python3 run.py "..."` live with all three real stations.
4. Fix any seam, tag the demo, then each group member clones `main` and walks away with a working AI CMO.
