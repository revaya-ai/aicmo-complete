# AI CMO — Reference Architecture (QA source of truth)

> This is the checklist the QA agents audit the repo against. It is the neutral, product-level spec of what a complete AI CMO must contain, derived from the AI CMO reference (the public deck and the full system map presented at the June 2026 mastermind). It does not reproduce any private material or name any third-party clients.
>
> The QA principle (Ben's Bali QA approach): the agent that checks is never the agent that built, and you watch for silence, not just errors. A component that is documented but absent, or a step that reports success while producing nothing, is a failure even when no error is thrown.

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
