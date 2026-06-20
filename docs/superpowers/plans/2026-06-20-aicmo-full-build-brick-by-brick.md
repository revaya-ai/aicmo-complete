# AI CMO — The Whole Build, Brick by Brick

> A complete, ordered build of the entire AI CMO. Each "brick" is the smallest unit that is independently buildable and demoable. Build them top to bottom and the pipeline grows one status at a time until a seed idea walks all the way to a live ad.
>
> Architecture: Claude Code skills + commands. The craft lives in skills, the loop runs through commands, small Python scripts are the runtime, `db.py` is the frozen contract. Client = `lumen-skin` demo. Platform = LinkedIn for the MVP.

---

## How to read this

Each brick has:
- **Brick** id + name
- **Reads -> Writes**: the pipeline status it consumes and the status it produces (the contract)
- **Files**: what to create or change
- **Does**: one line on the job
- **Done when**: the check that proves the brick works

Statuses (from `db.py`, frozen):
`captured -> drafted -> qc_review -> approved -> scheduled -> published -> analyzed -> ad_recommended -> ad_approved -> ad_live` (with `needs_revision` / `rejected` as off-ramps).

The genius of the order: every brick advances the post one more step, so you can demo the whole thing at any point up to the brick you have finished.

---

## Layer 0 — Foundation (DONE in scaffold)

- **B0.1 db.py contract** — the `posts` table + helpers (`create_post`, `advance`, `update_post`, `get_post`, `list_by_status`) + `Status` constants. Frozen. DONE.
- **B0.2 client context** — `client-data/lumen-skin/` six layers + `visual-brand.md` + `brand.css`. DONE (Brain refined voice rules).
- **B0.3 repo skeleton** — folders, `.gitignore`, `.env.example`, `requirements.txt`. DONE.

---

## Station 1 — BRAIN (Think + Write) — DONE, on branch `brain`

- **B1.1 save_draft.py + test** — reads nothing, **writes `drafted`**. Persists the four locked artifacts via the contract. DONE.
- **B1.2 writing-style skill** — anti-AI-slop rules + self-check. DONE.
- **B1.3 positioning-angles skill** — 10 named angles + how to choose. DONE.
- **B1.4 content-os skill** — the five-step Brick chain. DONE.
- **B1.5 ai-cmo-generate command** — runs the Brick chain, calls save_draft. **Done when** `ai-cmo-generate "<seed>"` produces an on-brand `drafted` record. DONE.

---

## Station 2 — STUDIO (Design + Check itself)

- **B2.1 visual-brand spec** — refine `client-data/lumen-skin/visual-brand.md` + `brand.css`: accent, bg, fonts, the "never" list, the rule that no text is model-generated on the image. **Done when** the spec names exact colors and fonts the renderer can read.

- **B2.2 post template** — `templates/social/post.html.j2`: a 1080x1350 layout using `brand.css` variables with `{{ hook }}` and `{{ body }}` slots. **Done when** the template renders with sample text and looks on-brand.

- **B2.3 render.py** — reads `drafted`, **sets `image_path`**. Fills the template, screenshots it with Playwright at 1080x1350 @2x, saves a PNG under `renders/`. **Done when** a test confirms a PNG of the right dimensions is produced and `image_path` is set on the row.

- **B2.4 brand-test skill** — the rubric a vision model scores against: layout, contrast, on-brand color use, legibility, no banned visual patterns. A 0 to 100 scale with the 85 pass line. **Done when** the rubric is concrete enough to score two images differently.

- **B2.5 brand_qc.py** — reads the rendered PNG, **writes `qc_review`** (pass) or **`needs_revision`** (fail). Sends the image to Claude vision, scores it against `brand-test`, returns score + notes. Gate at 85. **Done when** a test shows a good image passes to `qc_review` and a deliberately off-brand image routes to `needs_revision`.

- **B2.6 ai-cmo-render command** — orchestrates: load `brand-test`, run `render.py` then `brand_qc.py`, report the score. On `needs_revision`, regenerate the image (not the copy) and re-score, up to two tries. **Done when** `ai-cmo-render <post_id>` takes a `drafted` row to `qc_review` with a real score and image.

---

## Station 3 — MISSION CONTROL (Approve + Publish + Measure)

- **B3.1 gate.py (human gate)** — reads `qc_review`, **writes `approved`** or **`needs_revision`**. A Flask page listing `qc_review` rows (post text + image) with Approve / Reject. Reject captures `human_note`. **Done when** clicking Approve advances the row and Reject sends it back with a note. This is the one human decision, the heart of the product.

- **B3.2 schedule.py** — reads `approved`, **writes `scheduled`**. Picks a slot (simple: next weekday 09:00; better: from past engagement). Sets `scheduled_for`. **Done when** a test confirms an approved row gets a future `scheduled_for` and status `scheduled`.

- **B3.3 zernio.py** — a thin Zernio client wrapper. Real call if `ZERNIO_API_KEY` is set, otherwise a stub that returns a fake post URL. **Done when** it returns a URL in both modes without crashing.

- **B3.4 publish.py** — reads `scheduled`, **writes `published`**. Calls `zernio.py`, sets `published_url`. **Done when** a test (stub mode) advances a scheduled row to `published` with a URL.

- **B3.5 publish-linkedin skill** — platform-tuned rules: length, line breaks, no hashtag walls, first-line hook discipline. Loaded before publishing. **Done when** the skill states concrete LinkedIn formatting rules.

- **B3.6 ai-cmo-publish command** — orchestrates schedule + publish, loading `publish-linkedin`. **Done when** `ai-cmo-publish` takes an `approved` row to `published`.

- **B3.7 publish_check.py** — reads `published`, verifies the URL is live (stub: assume live). Logs a check. Cron every 30 min in production. **Done when** it runs without error and logs a verified check.

- **B3.8 analytics.py** — reads `published`, **writes `analyzed`**. Pulls metrics (stub: mock likes/comments/follows; real: Zernio analytics) into `metrics_json`. **Done when** a test advances a published row to `analyzed` with metrics.

- **B3.9 ai-cmo-engagement-sync command** — runs `publish_check` + `analytics`. **Done when** it takes a `published` row to `analyzed`.

- **B3.10 Notion mirror (STRETCH)** — mirror the pipeline to a Notion board so the client approves from their phone instead of the Flask page. Skip for the MVP, note it as the production surface. **Done when** rows appear in Notion with a status property (only if time allows).

---

## Station 4 — ADS (recommend-only) — assembled from all three builders

- **B4.1 ad-copy step (Brain contributes)** — a small `ad-copy` skill or a content-os branch that turns a winning post into ad-format copy (shorter, one clear CTA). **Done when** it produces ad copy from an `analyzed` post.

- **B4.2 ad-creative render (Studio contributes)** — `render.py` variant at ad dimensions. **Done when** it outputs an ad-sized image.

- **B4.3 ads_agent.py** — reads `analyzed`, **writes `ad_recommended`**. Detects winners (engagement over a threshold), writes a recommendation: `ad_target_post_id`, `ad_budget`, `ad_audience`. **Done when** a test shows a high-engagement post becomes `ad_recommended` and a low one does not.

- **B4.4 spend gate** — reads `ad_recommended`, **writes `ad_approved`**. Reuse `gate.py` with a spend-approval view. Sets `ad_spend_approved_by`. **Done when** approving a recommendation advances it.

- **B4.5 ads_push.py** — reads `ad_approved`, **writes `ad_live`**. Real Meta/LinkedIn Ads call if tokens set, otherwise stub returning a fake campaign id into `ad_status`. **Done when** an approved ad reaches `ad_live` in stub mode. (Real API is the stretch; stub is the floor. Ads auth must never block the content loop.)

- **B4.6 ai-cmo-ads command** — orchestrates recommend -> spend gate -> push. **Done when** `ai-cmo-ads` walks an `analyzed` winner to `ad_live`.

---

## Layer 5 — Integration + Polish

- **B5.1 orchestrator** — a thin `run.py` (or `ai-cmo-run` command) that walks one seed idea through every station entry point in order, printing each status transition. Reconciles the original Python stub loop to the skills+commands era. **Done when** one command takes a seed idea from `captured` to `ad_live` end to end.

- **B5.2 docs** — update `README.md` + add `CLAUDE.md` so a fresh clone knows how to run it. **Done when** a new person can clone and run from the README alone.

- **B5.3 live demo + merge** — merge `brain`, `studio`, `mission` into `main`, run the full loop live with a human approving in the middle. **Done when** the demo runs green on `main`.

---

## Build order if you are solo (the backup path)

The fastest path to a working end-to-end demo, one brick at a time:

1. Brain is done. You can already produce `drafted` posts.
2. B2.3 render + B2.5 brand_qc + B2.6 command. Now posts reach `qc_review`.
3. B3.1 gate. Now you can approve. Posts reach `approved`.
4. B3.3 zernio (stub) + B3.4 publish + B3.6 command. Posts reach `published`.
5. B3.8 analytics + B3.9 command. Posts reach `analyzed`.
6. B4.3 ads_agent + B4.4 spend gate + B4.5 push (stub) + B4.6 command. Posts reach `ad_live`.
7. B5.1 orchestrator ties it into one command. B5.2 docs. Done.

Polish bricks (B2.4 brand-test depth, B3.5 publish-linkedin, B3.10 Notion, real Zernio, real Ads API) are upgrades you layer on after the loop is green.

---

## What "done" means for the whole build

One command takes a typed seed idea and walks it: Brain writes the draft, Studio renders and QC-gates it, a human approves it, Mission Control publishes and measures it, and the Ads agent recommends promoting the winner for a second human approval. Every step is auditable in the `posts` table. That is the entire AI CMO, brick by brick.
