# Persona registry

The AI CMO works like a marketing department. Each role in that department is a persona. A persona is not a separate program. It is a named job, implemented by the skills that hold its craft, the commands that run its work, and the engine modules that do the work against the frozen contract.

This file makes the "works like a marketing department" framing concrete: it names every role and points to exactly what implements it.

## The department

| Persona role | What they own | Skills (craft) | Commands (the work) | Engine modules (runtime) |
|---|---|---|---|---|
| Analyst / Intelligence | Find what is worth writing about. Turn SEO, GEO, AEO, trends, and competitor signals into candidate seed ideas. | `intelligence` | `/ai-cmo-intel` | `engine/intelligence/intelligence.py` |
| Strategist | Pick the seed, choose the pillar and angle, lock the chain of decisions. | `content-os`, `positioning-angles` | `/ai-cmo-generate` | `engine/brain/generate.py`, `engine/save_draft.py` |
| Copywriter | Write the hook and the body in the client's voice. | `writing-style`, `hook-library`, `story-structures` | `/ai-cmo-generate` | `engine/brain/generate.py` |
| Creative / Designer | Render the post and the ad creative on brand. | `brand-test` | `/ai-cmo-render` | `engine/studio/render.py` (`run`, `render_ad`) |
| Systems / QA | Score the creative against the brand rubric and gate it. | `brand-test` | `/ai-cmo-render` | `engine/studio/brand_qc.py` |
| Publisher | Schedule, publish, verify, and measure. | `publish-linkedin` | `/ai-cmo-publish`, `/ai-cmo-engagement-sync` | `engine/mission/schedule.py`, `publish.py`, `zernio.py`, `publish_check.py`, `analytics.py` |
| Ads | Detect winners, recommend spend, push approved ads live. | `ad-copy` | `/ai-cmo-ads` | `engine/ads/ads_agent.py`, `ads_push.py`, `engine/studio/render.py` (`render_ad`) |
| Analyst (reporting) | Aggregate the pipeline, write the weekly brief, mirror the board. | (uses `feedback-loop` for the learning side) | `/ai-cmo-report` | `engine/dashboard/metrics.py`, `report.py`, `notion_mirror.py` |
| The human gate | The one human decision. Approve, reject, or request revision before publish, and approve ad spend. | (no skill; it is the human) | run the Flask gate, or `auto_approve` in `run.py` | `engine/mission/gate.py` (`approve`, `reject`, `request_revision`, `approve_spend`, `mirror_to_notion`) |

## The learning persona

The department also learns. The feedback loop is the persona that reads the measured results, names what won, and writes it back so the next draft is sharper.

| Persona role | Skills | Engine modules |
|---|---|---|
| Feedback / Learning | `feedback-loop` | `engine/feedback.py` |

## How a job flows through the personas

1. Analyst runs the sweep and hands seeds to the Strategist.
2. Strategist and Copywriter run the Brick chain and produce a draft.
3. Creative renders it. Systems / QA scores and gates it.
4. The human gate approves it.
5. Publisher schedules, publishes, and measures it.
6. Ads checks if it won and recommends spend for a second human approval.
7. Feedback harvests the winners back into the client learnings note.
8. The reporting Analyst writes the weekly brief.

Each persona reads the row at one status and advances it to the next. The frozen contract (`db.py`) is the shared desk every persona works on.

## The boundary

No persona writes another persona's fields. The Creative does not write metrics. The Publisher does not write the draft. This is the same discipline as the multi-repo model: clear edges between roles, enforced by the contract. See `docs/architecture/multi-repo-model.md`.
