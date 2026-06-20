# Architecture Fidelity Audit — AI CMO

**Auditor:** architecture-fidelity-auditor (independent; did not build this code)
**Date:** 2026-06-20
**Source of truth:** `docs/qa/reference-architecture.md` (sections A–L)
**Method:** Read every implementing file. Ran the loop live. Cross-checked the persona registry and brick plan against real files. Watched for silence as hard as for errors.

---

## TOP-LINE VERDICT: FAIL

PASS requires every component (A–L) to be PRESENT (real and wired). The system is structurally complete and the full loop runs end to end to `ad_live` offline with 47 passing tests, but **three components are PARTIAL**: the Brain (D) emits hardcoded copy with no client-context grounding, vision QC (E) does not inspect the image, and analytics (H) is mock-only with no real seam wired. None are SILENT or MISSING. The scaffold is honest about its env seams, but in the architecture's strongest sense ("every step produces a real artifact / does the work the architecture requires") the content-generation and QC brains do not yet do the work; they advance the row with placeholder logic.

**Verdict counts:** PRESENT 9 · PARTIAL 3 · SILENT 0 · MISSING 0

---

## Component table

| # | Component | Verdict | Evidence | Fix (if not PRESENT) |
|---|-----------|---------|----------|----------------------|
| A | Contract + loop | **PRESENT** | `db.py` defines all 12 statuses (`captured`→`ad_live`) plus `needs_revision`/`rejected` off-ramps. `run.py` walks one seed through every station. Live run printed every transition and ended at `ad_live`. Each station reads its input status and advances; no station writes another's fields (verified per-module). | — |
| B | Per-client 6-layer context | **PRESENT** | `client-data/lumen-skin/` holds all 6 layers (`positioning.md`, `brand-and-audience.md`, `strategy.md`, `offers.md`, `voice.md`, `guardrails.md`) plus visual spec (`visual-brand.md` + `brand.css`). Markdown, single source. | — |
| C | Intelligence layer | **PRESENT** | `engine/intelligence/intelligence.py` parses pillars from `strategy.md` and emits seed-idea dicts tagged by pillar and source. Real env seam (DATAFORSEO/GSC/APIFY) behind keys; deterministic offline bank by default. Does not advance rows (by design). `test_intelligence` passes. | — |
| D | Content engine (Think + Write) | **PARTIAL** | The brick chain is named (Intake→Topic→Angle→Hook→Story) and writes real distinct fields, so the row advances. But `engine/brain/generate.py` is all `TODO(builder)`: `pillar` is hardcoded `"Education"` regardless of seed, angle/hook/body are fixed f-strings, and the 6-layer context is **never loaded** (the load is a comment). No Claude call, no positioning/voice/guardrails grounding. The supporting craft skills exist (`writing-style`, `positioning-angles`, `hook-library`, `story-structures`) but nothing in the runtime invokes them. This is the closest thing in the repo to "documented but produces nothing real," softened only by the fact that it emits a real (if generic) draft. | Wire `generate.py` to load `client-data/<client>/*.md` and call Claude per brick (gated behind an env seam so offline still works). At minimum derive `pillar` from `strategy.md` instead of a constant. |
| E | Render + QC | **PARTIAL** | Render: PRESENT-ish — `render.py` fills the real HTML template and writes a valid 1080×1350 PNG; `image_path` is set; real Playwright path behind `AICMO_RENDER=playwright`. But the default artifact is a **solid-color placeholder PNG**, not a rasterization of the on-brand layout, so offline "render" produces no on-brand graphic. QC: the gate at 85 exists and routes pass→`qc_review` / fail→`needs_revision`, but `brand_qc._detect_off_brand()` only checks for a missing/empty file; it does **not** inspect the PNG against the brand spec by default (`score_image` is a pure constant: 90 clean / 60 off). The architecture's requirement ("a vision QC gate that scores every render against the brand spec") is not met offline; it is an env seam (`AICMO_VISION_QC=claude`). | Make the default render rasterize the template (or document that the placeholder is not the deliverable). Wire a real vision scorer behind the existing `AICMO_VISION_QC` seam so the score reflects the actual pixels. |
| F | Human gate | **PRESENT** | `engine/mission/gate.py` is a real Flask app listing `qc_review` rows with Approve/Reject/Revise; reject captures `human_note`. `approve_spend` handles the ad gate. `auto_approve=True` in `run.py` drives the demo. Central, real, phone-reviewable via Notion mirror. | — |
| G | Distribution | **PRESENT** | `schedule.py` (next-weekday 09:00 slot, sets `scheduled_for`), `publish.py`→`zernio.py` (stub URL offline, real call behind `ZERNIO_API_KEY`), `publish_check.py` verifies live. Live run produced a real `published_url`. Tests pass. | — |
| H | Analytics + feedback | **PARTIAL** | Feedback is PRESENT: `engine/feedback.py` ranks `analyzed` posts by engagement rate and appends real winners to `client-data/<client>/learnings.md` (tests confirm append-not-overwrite). But analytics is mock-only: `analytics.py` calls `mock_metrics()` in **both** branches — the `ZERNIO_API_KEY` branch is a comment, not a real call. The "pull engagement back after publishing" requirement is simulated, not seamed to a real source. | Implement the real Zernio analytics call in the keyed branch of `analytics.py` (currently identical to the stub). |
| I | Ads (recommend-only) | **PRESENT** | `engine/ads/ads_agent.py` detects winners by engagement *rate* (pure testable functions), writes `ad_recommended` with budget/audience, gates spend via `gate.approve_spend`, then `ads_push.py`→`ad_live`. Real Meta/LinkedIn behind tokens; stub campaign id offline. Spend never happens without the gate. Live run reached `ad_live` as a winner. | — |
| J | Dashboard + reporting | **PRESENT** | `engine/dashboard/metrics.py` (pipeline metrics), `report.py` (weekly brief markdown — `test_dashboard` confirms file written), `notion_mirror.py` (board mirror; JSON to `outputs/notion-mirror.json` offline, real Notion behind `NOTION_TOKEN`). | — |
| K | Multi-repo / IP boundary | **PRESENT** | `engine/leak_guard.py` walks a client box, regex-matches every *other* roster client's slug + spaced variants across text files, returns a list of `{file, match, line}`. Verified live: clean scan of `lumen-skin` against a 3-client roster returned `[]`. `docs/architecture/multi-repo-model.md` documents the one-engine/one-data-repo rule. `test_leak_guard` passes. | — |
| L | Marketing-department framing | **PRESENT** | `docs/architecture/agents.md` maps every persona (Analyst, Strategist, Copywriter, Creative, Systems/QA, Publisher, Ads, reporting Analyst, human gate) to concrete skills + commands + engine modules. Every named module path resolves to a real file (verified). 10 skills in `.claude/skills/`, 8 `ai-cmo-*` commands in `.claude/commands/`. | — |

---

## Cross-cutting requirements

- **Anyone can use it (offline, no keys):** PASS. Fresh clone, `python3 run.py "..."` walks `captured`→`ad_live` on the stdlib alone. Real integrations all sit behind env seams (`AICMO_RENDER`, `ZERNIO_API_KEY`, `NOTION_TOKEN`, `DATAFORSEO_LOGIN`, etc.).
- **Auditability:** PASS. Every transition is a real row update; the final row carries `image_path`, `published_url`, `metrics_json`, `ad_status`, `human_note`.
- **No silence:** MOSTLY PASS. Every step that reports success produces a real artifact (real PNG file, real row, real report/learnings file). The caveat: the *content* of two of those artifacts (the draft copy in D, the QC score in E) is placeholder logic, not the work the architecture describes. No step lies about producing a file.
- **IP clean:** PASS. Demo client is the fictional `lumen-skin`; no third-party or peer client names found. Leak guard enforces this structurally.
- **Voice discipline:** Not separately re-audited here (belongs to the voice/content QA pass); the `writing-style` skill encodes the anti-AI-slop rules but is not invoked by the runtime (see D).

---

## Persona registry + brick plan cross-check

Every role in `docs/architecture/agents.md` and every brick (Layer 0 → Layer 6) in `docs/superpowers/plans/2026-06-20-aicmo-full-build-brick-by-brick.md` maps to a real file that exists on disk. No phantom modules. The gaps are not missing files — they are real files whose default logic is placeholder (D, E, H).

---

## The single most important fix

**Wire `engine/brain/generate.py` to actually load the 6-layer client context and generate grounded copy (behind an env seam).** Today the Brain — the "Think + Write" heart of a content marketing department — ignores `client-data/` entirely and emits a hardcoded pillar plus fixed-template copy. Everything downstream (render, QC, publish, ads, learnings) operates on placeholder content. This is the one gap that most undermines the product's core claim, and fixing it lights up the craft skills that already exist.
