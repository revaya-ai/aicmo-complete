# AI CMO: Reference Architecture (QA source of truth)

> This is the checklist the QA agents audit the repo against. It is the neutral, product-level spec of what a complete AI CMO must contain, derived from the AI CMO reference (the public deck and the full system map from a reference architecture). It does not reproduce any private material or name any third-party clients.
>
> The QA principle (an independent-QA approach): the agent that checks is never the agent that built, and you watch for silence, not just errors. A component that is documented but absent, or a step that reports success while producing nothing, is a failure even when no error is thrown.

---

## The one-line definition

A content marketing department that runs as software. One seed idea goes in. The system thinks, writes, designs, checks itself, waits for a human at exactly one point, then ships and measures. Six steps run themselves. The seventh is a person.

## Required components

### A. The contract and the loop
- A frozen content record (`db.py`) with the full status pipeline: `captured -> drafted -> qc_review -> approved -> scheduled -> published -> analyzed -> ad_recommended -> ad_approved -> ad_live`, plus `needs_revision` and `rejected` off-ramps.
- An orchestrator that walks one seed idea through every status (`run.py`).
- Every station reads its input status and writes its output status. No station writes another station's fields.

### B. Per-client context (the 6-layer contract)
- Six markdown layers per client: positioning, brand-and-audience, strategy, offers, voice, guardrails.
- A visual brand spec (visual-brand.md + brand.css).
- The brand lives in markdown so every agent in the loop reads the same source.

### C. Intelligence layer (front of funnel)
- SEO, GEO, AEO, trends, and competitor signals turned into candidate seed ideas, feeding the strategist.

### D. Content engine (Think + Write)
- The Brick chain: Intake, Topic and pillar, Angle, Hook, Story and shift. Each step locks before the next.
- Supporting craft skills: writing-style (anti-AI-slop), positioning-angles, hook library, story structures.
- Output: an on-brand drafted post.

### E. Render and QC (Design + Check itself)
- Render the on-brand graphic from the brand spec. No text is written by the image model; all copy lands through the template.
- A vision QC gate that scores every render against the brand spec. Off-brand output never reaches the human. Pass line at 85.

### F. The human gate (the one decision)
- A single approve or reject decision, reviewable from a phone. Reject captures a note and routes to revision.
- The gate is the heart of the product. It must be real and central, not an afterthought.

### G. Distribution (Ship)
- Schedule by best time, publish through one publishing layer, verify it actually went live.

### H. Analytics and feedback (Measure and learn)
- Pull engagement back after publishing.
- Harvest winners and feed the language and angles back into the client context so the next draft lands closer.

### I. Ads (recommend-only)
- Watch winners, recommend a promotion with budget and audience, gate the spend with a second human approval, then push. Recommend-only by design. Spend never happens without a human.

### J. Dashboard and reporting
- A client-facing surface (a board the client approves from) and reporting (a weekly brief, a metrics summary).

### K. The multi-repo / IP boundary
- One engine, one private data repo per client, they never mix.
- A client box contains no other client's name. A leak guard enforces this structurally.

### L. The marketing-department framing
- The roles (analyst, strategist, copywriter, creative, systems/QA, publisher, ads, plus the human) map to concrete skills, commands, and modules.

## Cross-cutting requirements

- **Anyone can use it.** A fresh clone runs from the README alone, offline, with no API keys. Real integrations sit behind env seams.
- **Voice discipline.** No em dashes or hyphens used as breaks. No banned AI-slop phrases. Show, do not claim. One idea per post.
- **Auditability.** Every step is traceable in the content record.
- **No silence.** Every step that reports success produces a real artifact (a real image file, a real record row, a real report file).
- **IP clean.** No copied third-party material, no peer or third-party client names in the repo.

## Named-Integration Register

This register is part of the QA source of truth. The reference architecture above is deliberately tool-agnostic, so a structurally-blind audit could not see when a concrete, named integration was missing. This table closes that gap by listing every concrete external tool the system uses or that the source materials named. Any new external integration must be added here. The architecture-fidelity auditor checks every WIRED row against the repo to confirm the module exists and is gated, and confirms every NOT BUILT row is a known gap rather than a silent miss.

| Tool | Function | Env seam | Stub/offline behavior | Status in code |
|---|---|---|---|---|
| Anthropic (Claude) | Station 1 (Brain) text generation for the content chain. | `ANTHROPIC_API_KEY` | The brain generator (`engine/brain/generate.py`) uses no API and runs deterministic offline. The env var is declared in `.env.example` but not consumed by code. | STUB-ONLY |
| Placid | Station 2 (Studio) on-brand template composite images, so all type lands through the template, never written by an image model. | `PLACID_API_TOKEN`, `PLACID_TEMPLATE_UUID` (optional default) | `PlacidClient` raises `PlacidNotConfigured` before any network call when the token is absent; `engine/studio/render.py` catches it and falls back to the offline render (PIL default, then stdlib placeholder PNG). Real path only taken when `AICMO_RENDER=placid` and the token is set. | WIRED |
| Gemini / Nano Banana | Image model option for Studio render. | none | Not gated by any env var. No client module in the repo. Render uses PIL/stdlib by default and Placid or Playwright as the only opt-in real paths. | NOT BUILT |
| Playwright | Station 2 (Studio) HTML/CSS template screenshot render at 1080x1350 @2x. | `AICMO_RENDER=playwright` (selector, not a credential) | Only taken when `AICMO_RENDER=playwright` and Playwright is importable; otherwise falls back to PIL default, then stdlib placeholder. Offline by default. | WIRED |
| Zernio | Station 3 (Mission) one publishing API to LinkedIn, IG, and X, plus analytics pull. | `ZERNIO_API_KEY` | `engine/mission/zernio.py` returns a deterministic fake post URL when the key is absent. Real API call only when the key is set. | WIRED |
| Meta Ads | Station 4 (Ads) recommend-only Meta ad campaign creation. | `META_ACCESS_TOKEN` (consumed in `engine/ads/ads_push.py`, declared in `.env.example`) | Returns a stable stub campaign id when no token is set; real campaign only when the token is present. | WIRED |
| LinkedIn Ads | Station 4 (Ads) recommend-only LinkedIn ad campaign creation. | `LINKEDIN_ACCESS_TOKEN` (consumed in `engine/ads/ads_push.py`, declared in `.env.example`) | Returns a stable stub campaign id when no token is set; real campaign only when the token is present. | WIRED |
| DataForSEO | Intelligence and AEO layer SEO/AEO/LLM-visibility signals. | `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` (both required) | `DataForSEOClient` raises `DataForSEONotConfigured` before any network call when either credential is missing; the Intelligence layer falls back to a deterministic offline stub. | WIRED |
| GSC (Google Search Console) | Intelligence layer search-console signals. | `GSC_CREDENTIALS` (named in `engine/intelligence/intelligence.py` docstring only) | No client module, no real gating. Only DataForSEO is actually wired in the Intelligence layer; GSC is documented intent, not built. | NOT BUILT |
| Apify | Intelligence layer competitor scrapes. | `APIFY_TOKEN` (named in `engine/intelligence/intelligence.py` docstring only) | No client module, no real gating. Documented intent, not built. | NOT BUILT |
| Notion | Station J client surface: pipeline DB, approval board, dashboard mirror. | `NOTION_TOKEN` | `engine/dashboard/notion_mirror.py` writes a local JSON board (`outputs/notion-mirror.json`) when the token is absent; pushes to a Notion database when set. | WIRED |
| Backblaze B2 | Nightly encrypted backups and the client no-AI-image asset store. | none | No client module, no env var declared. Backup integrity and the real-image asset store are uncaptured. | NOT BUILT |
