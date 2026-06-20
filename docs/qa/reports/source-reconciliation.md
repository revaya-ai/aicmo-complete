# Source Reconciliation Audit — Jen's AI CMO vs. reference-architecture.md

**Auditor role:** Independent source-reconciliation. I did not build this system. I diffed what Jen Bourke actually said/showed (3 primary sources) against the spec the implementation QA audited against (`docs/qa/reference-architecture.md`).

**Sources of truth:**
1. `knowledge/resources/2026-06-18-jen-ai-cmo-bali.md` (Jen AI CMO brief)
2. `knowledge/wiki/people/jennifer-bourke.md` (profile — thin, stub)
3. `bali/hackathon-ai-cmo-build-plan.md` (build plan, early decisions)

**Spec under audit:** `/Users/short/Downloads/aicmo-complete/docs/qa/reference-architecture.md` (67 lines, deliberately tool-agnostic).

---

## VERDICT

**7 MISSED, 8 PARTIAL.**

The reference architecture names almost no concrete vendor. Grep confirms: Placid 0, Zernio 0, Notion 0, DataForSEO 0, GSC 0, Apify 0, Gemini 0, Playwright 0, Backblaze 0, Data Jumbo 0 mentions. It describes *capabilities by function* ("a client-facing surface," "render the on-brand graphic"). That design choice is the structural blind spot: when a real integration (Placid) is named only in the source and never in the spec, the implementation QA cannot test for it. Placid is not a one-off miss; it is a *class* of miss.

**Important nuance:** "MISSED" here means the spec does not capture a concrete, named, behavior-bearing thing Jen described — not merely a vendor brand. Generic-capability coverage is scored PARTIAL.

---

## DIFF TABLE

| Item | Source quote + location | Status | Note |
|---|---|---|---|
| **Placid (image-template composites)** | brief Key Points: "all type goes through Placid templates"; build-plan tech stack: "Placid optional for composites"; brief Implications: "Placid (template rendering, no AI text on images)" | **MISSED** | Confirmed: 0 mentions in spec. The known structural gap. Spec says "all copy lands through the template" but never names Placid as the composite/template service, so QA could not detect the missing integration. |
| **publish_check.py — 30-min live verification** | brief: "`ai_cmo_publish_check` (verifies live every 30 min)" | **MISSED** | Spec's Distribution section (G) says only "ship." No mention of a post-publish liveness watchdog. Implementation has it (`engine/mission/publish_check.py`) but spec never required it — invisible to QA. |
| **engagement_sync nightly + cron times 06:30/18:30** | brief: "`ai_cmo_publish` (cron 06:30 / 18:30)", "`ai_cmo_engagement_sync` (pulls metrics nightly)" | **MISSED** | Spec H ("pull engagement back") omits cadence/scheduling entirely. No cron, no 06:30/18:30, no nightly sync in spec. 0 mentions. |
| **Voice of Customer as Brick Phase 0** | brief: "Phase 0 starts with Voice of Customer (updated per Jamie's advice)" | **MISSED** | Spec D lists Brick chain as "Intake, Topic and pillar, Angle, Hook, Story and shift." VoC/Phase 0 is absent. A named, ordered first step Jen explicitly added is not in the spec. |
| **brand-test (3-way visual bake-off skill)** | brief: "Skills: ... `brand-test` (3-way visual bake-off)" | **MISSED** | 0 mentions. Spec E describes a single vision QC gate, not a comparative 3-way bake-off skill. Distinct behavior, uncaptured. |
| **Backblaze B2 encrypted backups + no-AI-image asset store** | brief: "Backblaze B2 (nightly encrypted backups, also stores client no-AI-image assets)" | **MISSED** | 0 mentions. Spec K covers IP boundary but not backup/asset storage. The "no-AI-image asset store" is a real content behavior, not just infra. |
| **Run economics / ~$0.02 per post tiering** | brief: "Run economics (~$0.02/post)", "$20/$50/$110/mo tiers", "bill is set by ambition, not headcount" | **MISSED** | 0 mentions of economics/0.02/tiers. Not a build requirement per se, but a defining product claim Jen led with; absent from the "source of truth." |
| **5-step daily loop ("seven-step model")** | brief: "5-step daily loop: Thinks → Writes & designs → Checks itself → Waits for a human → Ships & measures" | PARTIAL | Spec's one-liner captures the loop ("thinks, writes, designs, checks itself, waits for a human, ships and measures") — faithful, but frames it as 6+1 steps without naming the 5-step daily-loop model Jen used. Conceptually present, labeling lost. |
| **7-state Notion pipeline / status enum** | brief: "captured → drafted → qc_review → approved → scheduled → published → analyzed"; build-plan adds needs_revision/rejected/ad_* | CAPTURED | Spec A reproduces the full enum incl. ad_recommended/ad_approved/ad_live and off-ramps. Strong match. |
| **Notion (client surface: pipeline DB, approval board, dashboard)** | brief Toolstack: "Notion (pipeline/approvals/reports)"; build-plan: "approve from a Notion board" | PARTIAL | Spec J abstracts to "a client-facing surface" + "reporting." Notion never named. Capability captured; the actual surface Jen ships on is not, so a Notion-specific integration gap would be invisible. |
| **Data Jumbo charts** | brief: "Data Jumbo (charts)"; build-plan: "live dashboard (Data Jumbo charts)" | PARTIAL | Spec J says "metrics summary." The named charting tool is absent. Same blind-spot class as Placid (lower risk). |
| **Intelligence sources: DataForSEO, GSC, Apify, SEO/GEO/AEO/trends/competitor** | brief Toolstack + build-plan tech stack; brief: "Intelligence layer (SEO·GEO·AEO·trends·competitor watch)" | PARTIAL | Spec C captures "SEO, GEO, AEO, trends, and competitor signals ... feeding the strategist" — categories yes, named tools (DataForSEO/GSC/Apify) no. Implementation wires them via env vars; spec wouldn't catch a missing one. |
| **Image render: Gemini/Nano Banana + Playwright HTML/CSS** | build-plan tech stack: "Gemini / Nano Banana ... Playwright + HTML/CSS templates"; brief: "Gemini never writes text on images" | PARTIAL | Spec E captures the *rule* ("no text written by the image model; all copy lands through the template") but names no renderer. Behavior captured, tools not. |
| **Zernio (one publishing API → LinkedIn/IG/X + analytics)** | build-plan: "Zernio (confirmed). One API to LinkedIn/IG/X + analytics pull"; brief Toolstack | PARTIAL | Spec G says "ship" / distribution only — never names Zernio, the multi-platform fan-out, or the analytics-pull side of it. Implementation has `zernio.py` (stub). Capability thinly captured; named integration not. |
| **8 agent personas (Ben/Edgar/Laura/Nataliya/Shannon/Tyler/Shubs/Valera)** | brief: "Agent team (8 personas): Ben (Strategist), Edgar (Content), Laura (Copy), Nataliya (Creative), Shannon (Systems/QA), Tyler (Analyst), Shubs (Publisher), Valera (human approves)" | PARTIAL | Spec L ("marketing-department framing") references roles generically (Strategist 2x, Publisher 1x, Analyst 1x) but names zero personas and omits the 8-role roster + Tyler's weekly feed-to-strategist behavior. Department concept captured; the registry is not. |
| **Meta + LinkedIn Ads (recommend-only, 4th station)** | build-plan paid ads module; brief Toolstack | CAPTURED | Spec I ("Ads (recommend-only)") + status enum cover this. Match. |
| **6-layer per-client context + brand-as-markdown** | brief: positioning/brand-and-audience/strategy/offers/voice/guardrails + visual-brand.md/brand.css | CAPTURED | Spec B reproduces all six layers + visual brand spec. Match. |
| **3-repo / structural IP isolation + leak guard + offboarding** | brief: "Architecture (3 repos) ... structural, not contractual ... a guard blocks it"; "Offboarding: switch off, hand client their data" | PARTIAL | Spec K captures one-engine/one-data-repo + leak guard. Drops the explicit 3-repo (AIOS→Core→Client VPS) topology, nightly one-way sync, and offboarding hand-back behavior. |
| **Vision QC ≥85 pass line** | brief: "Vision QC must score ≥85" | CAPTURED | Spec E: "Pass line at 85." Match. |
| **content-os skill name (Brick)** | brief: "Skill is named `content-os`" | PARTIAL | Spec D names "the Brick chain" (1 mention) but not the `content-os` skill name. Minor. |

---

## HIGHEST-RISK GAPS (MISSED, priority order)

1. **Placid** — the original blind spot. A real, named template/composite integration with a specific behavioral contract ("all type goes through Placid"). Confirmed 0 mentions. Any others in this class are equally untestable.
2. **publish_check.py (30-min live verification watchdog)** — a real reliability behavior Jen named; the spec's distribution section stops at "ship." Implementation built it; QA never required it.
3. **engagement_sync + cron cadence (06:30/18:30, nightly)** — the analytics loop has no scheduling requirement in the spec, so "no silence / real artifact" guarantees aren't enforced on a timeline.
4. **Voice of Customer (Brick Phase 0)** — an explicit, ordered first reasoning step Jen *added on advice*. Its absence means the content engine could pass QA while skipping the step Jen treats as foundational.
5. **brand-test (3-way visual bake-off)** — a distinct creative-selection behavior collapsed into the single QC gate.
6. **Backblaze B2 backups + no-AI-image asset store** — backup integrity and the client-supplied real-image library are uncaptured.
7. **Run economics / $0.02-per-post tiering** — the product's headline value claim; not a build gate but absent from the source of truth.

---

## TRUSTWORTHINESS OF reference-architecture.md AS A QA SOURCE OF TRUTH

**It is trustworthy for the *shape* of the system and untrustworthy for the *concrete integrations and named behaviors*.**

The spec is a clean, faithful abstraction of Jen's architecture: the contract, the status enum, the 6-layer context, the human gate, the QC≥85 line, and the recommend-only ads station are all captured accurately. Implementation QA run against it will correctly verify the loop's skeleton.

But the spec was written tool-agnostic by design, and that is precisely what created the Placid miss. Every concrete integration Jen named is either absent (Placid, Data Jumbo) or reduced to a generic capability (Zernio, Notion, DataForSEO, Gemini/Playwright). Worse, several *behaviors* — not just vendor names — never made it in at all: the 30-min publish_check watchdog, the engagement-sync cadence, VoC Phase 0, brand-test, and the Backblaze asset store. These are functional requirements that a structurally-blind QA pass will silently skip.

**Recommendation:** the reference architecture does **not** need a full rewrite, but it needs a **source-driven appendix** before it can be the sole QA anchor. Add (a) a named-integration register (tool → function → env seam → stub behavior) so each real integration is individually testable, and (b) the missed behaviors (publish_check, engagement_sync cadence, VoC Phase 0, brand-test, Backblaze) as explicit components. Until then, treat any "all green" implementation QA as *necessary but not sufficient* — it proves the loop runs, not that the system matches what Jen actually built.
