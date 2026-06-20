# Brand and Voice Fidelity Audit

Independent QA. Auditor did not build this code. Run date: 2026-06-20.

Source of truth: `docs/qa/reference-architecture.md`, `client-data/lumen-skin/voice.md`,
`client-data/lumen-skin/guardrails.md`, `.claude/skills/writing-style/SKILL.md`.

## Top-line verdict: FAIL

Two of the three non-negotiables fail. Voice discipline fails on em dashes inside
real client-data content and a live template. IP cleanliness fails on third-party
and peer personal names in the repo. The human gate passes. FAIL stands until the
em dashes in client-data + template are removed and the names are scrubbed.

---

## 1. Em-dash findings

The voice rule (voice.md line 15, writing-style line 14, reference-architecture
line 64) is a hard rule: no em dashes or hyphens used as breaks. Findings are
ranked by severity. A hit inside a quoted example in a planning/spec doc is
acceptable; a hit in client content, a template, or a real heading is a finding.

### CRITICAL — client-data content (the brand's own files break the brand's own rule)
These ship as the client voice contract. They MUST be clean.

- `client-data/lumen-skin/voice.md:1` — `# Voice — Lumen Skin Studio`. Fix: `# Voice: Lumen Skin Studio` or `# Voice, Lumen Skin Studio`.
- `client-data/lumen-skin/guardrails.md:1` — `# Guardrails — Lumen Skin Studio`. Fix: replace ` — ` with `: `.
- `client-data/lumen-skin/visual-brand.md:1` — `# Visual Brand — Lumen Skin Studio`. Fix: `: `.
- `client-data/lumen-skin/brand-and-audience.md:1` — `# Brand & Audience — Lumen Skin Studio`. Fix: `: `.
- `client-data/lumen-skin/brand-and-audience.md:9` — `**"Overwhelmed Olivia"** — 32, works full time...`. Fix: replace ` — ` with `, `.
- `client-data/lumen-skin/brand-and-audience.md:15` — `**"Skeptical Sam"** — 28, tried everything...`. Fix: replace ` — ` with `, `.
- `client-data/lumen-skin/strategy.md:1` — `# Content Strategy — Lumen Skin Studio`. Fix: `: `.
- `client-data/lumen-skin/strategy.md:13` — `1. **Education (40%)** — teach...`. Fix: replace ` — ` with `. `.
- `client-data/lumen-skin/strategy.md:14` — `2. **Proof (25%)** — before/afters...`. Fix: `. `.
- `client-data/lumen-skin/strategy.md:15` — `3. **Behind the studio (20%)** — the two founders...`. Fix: `. `.
- `client-data/lumen-skin/strategy.md:16` — `4. **Offers (15%)** — the starter set...`. Fix: `. `.
- `client-data/lumen-skin/positioning.md:1` — `# Positioning — Lumen Skin Studio`. Fix: `: `.
- `client-data/lumen-skin/offers.md:1` — `# Offers — Lumen Skin Studio`. Fix: `: `.
- `client-data/lumen-skin/offers.md:3` — `## Core offer: The Starter Set — $68`. Fix: `Starter Set, $68`.
- `client-data/lumen-skin/offers.md:16` — `**"The 3-Product Routine"** — a free one-page guide...`. Fix: replace ` — ` with `, `.

### CRITICAL — live template (renders into shipped graphics path)
- `templates/social/post.html.j2:1` — comment `{# Lumen Skin Studio — social post template ... #}`. Fix: replace ` — ` with `, `. (Comment only, does not render, but it is a real break in a production template file.)

### HIGH — repo content / headings (skills, briefs, README-tier docs)
- `ASSIGNMENTS.md` lines 1, 33, 39, 44, 46, 57, 71, 83, 88, 92 — em dashes used as real breaks in card titles and bullets. Replace each ` — ` with `: `, `, `, or `. `.
- `TEAM-BRIEF.md` lines 1, 43, 49, 55 — em dashes in title and card headings. Fix: `: `.
- `docs/qa/reference-architecture.md:1` — `# AI CMO — Reference Architecture`. This is the QA source of truth; the heading itself uses a break. Fix: `: `.

### ACCEPTABLE (no fix required)
- `.claude/agents/qa/brand-voice-fidelity-auditor.md:22` — em dash appears inside the quoted grep command and rule discussion. Spec discussing the rule. OK.
- `docs/superpowers/plans/2026-06-20-card1-brain.md` lines 1, 23 + grep-command lines 179/202/226/258 — planning doc; em dashes in section titles are real breaks but this is an internal plan, borderline. Recommend fixing titles on next pass.
- `docs/superpowers/specs/2026-06-20-card1-brain-design.md` lines 1, 27, 29, 37, 39, 43, 65 — spec doc; same borderline status. Recommend fixing on next pass.
- Python module docstrings (`engine/**/*.py`, `tests/**/*.py`, e.g. `STATION 2 — Studio`) — ~18 hits in docstring titles. Not shipped copy, but they are real breaks. LOW priority; recommend converting to `: ` for full consistency.

**Em-dash finding count (CRITICAL + HIGH, client-data/template/skill/brief/heading): 31.**
Plus ~25 LOW/borderline hits in spec, plan, and Python docstrings.

---

## 2. Banned-phrase findings

Scanned client-data files, `templates/social/post.html.j2`, and the brain draft body
against the writing-style banned list and voice.md "never use" list.

- **No banned phrases found** in client-data content, the template, or the generated draft body.
- Note: client-data files reference banned/never words only as words the brand avoids
  (e.g. guardrails.md and voice.md list "miracle", "revolutionary", "clinically proven"
  as prohibited). These are rule definitions, not usage. Not findings.

**Banned-phrase finding count: 0.**

---

## 3. Human-gate verdict: PASS (gate cannot be bypassed)

A post cannot reach `published` without a real approve decision, and spend cannot
reach `ad_live` without a second approval.

Evidence:
- `engine/mission/gate.py:34-47` — `run(post_id, auto_approve=False)` does NOT advance.
  With `auto_approve=False` it raises `RuntimeError`, refusing to move the post.
  The only paths to `Status.APPROVED` are `approve()` (gate.py:19-21), called either
  by the Flask human action (`/decide`, lines 86-92) or by the explicit demo
  `auto_approve=True` branch (lines 37-39). Auto-approve in the demo is sanctioned by
  the charter and the reference architecture (line 38).
- The pipeline cannot skip the gate: each station reads its specific input status.
  `engine/mission/publish.py:3` reads `status == scheduled`; `schedule` reads
  `approved`; so a post must pass through the gate's `approved` write to ever be
  scheduled or published. `run.py:56-63` walks stations in fixed order.
- Spend gate: `engine/ads/ads_agent.py:94-101` — if `not auto_approve`, it stops at
  `ad_recommended` and returns. Going live requires `approve_spend()`
  (gate.py:130-132, advances `ad_recommended -> ad_approved`) before
  `ads_push.run()`. The Flask spend gate (`/spend/decide`, gate.py:116-125) is the
  human path. No code path pushes an ad live without `approve_spend` first.

Caveat (not a gate bypass, flagged for hardening): `db.advance()` (db.py:188-195)
validates only that the target status is a member of `STATUSES`. It does not enforce
a legal transition graph, so a future caller could in principle jump statuses. Today
the pipeline ordering and per-station input checks make this safe, but a transition
whitelist in `advance` would make the gate structurally tamper-proof. Recommended, not blocking.

---

## 4. Show-dont-claim findings

Spot-checked the generated draft body (`engine/brain/generate.py:44-50`) and the
render template.

- No invented statistics. No unbacked numeric claims. The draft uses "three things",
  "four weeks" which are voice-approved framings (voice.md line 19) and are directional,
  not fabricated performance data.
- Minor soft-claim language: "That is the whole secret" and "Simple beats fancy.
  Every time." (generate.py:49-50) lean slightly promotional and absolute. Within
  brand tolerance (dry, blunt), not a violation. The body is a documented stub
  (`TODO(builder)` lines 22-43); the real grounded generator is unbuilt.

**Show-dont-claim finding count: 0 violations. 1 stylistic watch-item.**

---

## 5. IP-cleanliness verdict: FAIL

The leak guard passes structurally, but third-party and peer personal names are
present in repo text. The charter forbids "peer or third-party client names in the repo."

- `engine/leak_guard.py` run against `client-data/lumen-skin --clients lumen-skin`:
  **CLEAN** (no foreign client names in the client box). The structural client-box
  boundary holds.
- BUT third-party / peer personal names leaked into docs and briefs:
  - `TEAM-BRIEF.md:11` — "We are rebuilding the version **Jen** demoed". Third-party
    person named. Fix: remove the name. e.g. "We are rebuilding the AI CMO reference
    so we all walk away with a working copy."
  - `docs/superpowers/plans/2026-06-20-card1-brain.md:18` — "written from **Jen's**
    public deck concepts". Fix: "written from the public AI CMO deck concepts".
  - `docs/superpowers/specs/2026-06-20-card1-brain-design.md:27` — "original, written
    from **Jen's** public deck". Fix: same as above.
  - `docs/qa/reference-architecture.md:5` — "**Ben's** Bali QA approach". Peer name.
    Fix: "the Bali QA approach" or "the independent-auditor QA approach".
- No copied transcript text detected. No third-party client names detected
  (scanned for ZeroArc, Bourke, and others — none present).

**IP-cleanliness verdict: FAIL.** Two distinct names (Jen, Ben) across 4 files.
Structural leak guard is clean; the failure is named individuals in prose.

---

## Summary of required fixes (to move FAIL -> PASS)

1. Remove all em dashes used as breaks from the 15 `client-data/lumen-skin/*.md`
   hits and the `templates/social/post.html.j2` comment. (CRITICAL.)
2. Scrub the names "Jen" (3 files) and "Ben" (1 file) from all repo text. (CRITICAL.)
3. Fix em dashes in `ASSIGNMENTS.md`, `TEAM-BRIEF.md`, and the
   `reference-architecture.md` heading. (HIGH.)
4. Optional hardening: add a legal-transition whitelist to `db.advance()`.
5. Optional consistency: convert Python docstring-title em dashes to colons.
