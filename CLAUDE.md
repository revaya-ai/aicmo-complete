# CLAUDE.md

Guidance for Claude Code working in this repository: the AI CMO.

## What this is

A content marketing department that runs as software. One content idea is one row
in a SQLite table. The row walks a status pipeline. Each station reads the row at
one status, does its job, and advances it to the next. The craft lives in skills,
the loop runs through commands, small Python modules are the runtime, and `db.py`
is the frozen contract.

The whole thing runs offline on the Python standard library with no API keys.
Every external service has a stub that runs by default and only calls the real
service when its env var is set.

## The frozen contract

`db.py` is the single shared contract. Do NOT change the schema, the `Status`
values, or the helper signatures. Every station imports from here.

Helpers: `init_db()`, `create_post(client, seed_idea, platform="linkedin")`,
`get_post(id)`, `update_post(id, **fields)`, `list_by_status(status)`,
`advance(post_id, new_status, **fields)`.

Status pipeline:

```
captured -> drafted -> qc_review -> approved -> scheduled
         -> published -> analyzed -> ad_recommended -> ad_approved -> ad_live
```

Off-ramps: `needs_revision`, `rejected`.

Rule: each station writes ONLY its own fields and advances to its own output
status. Never write another station's columns.

## The stations

| Station | Folder | Reads -> Writes | Key modules |
|---|---|---|---|
| 1. Brain | `engine/brain/` | `captured` -> `drafted` | `generate.py`, `engine/save_draft.py` |
| 2. Studio | `engine/studio/` | `drafted` -> `qc_review` / `needs_revision` | `render.py`, `brand_qc.py` |
| 3. Mission | `engine/mission/` | `qc_review` -> `approved` -> `scheduled` -> `published` -> `analyzed` | `gate.py`, `schedule.py`, `zernio.py`, `publish.py`, `publish_check.py`, `analytics.py` |
| 4. Ads | `engine/ads/` | `analyzed` -> `ad_recommended` -> `ad_approved` -> `ad_live` | `ads_agent.py`, `ads_push.py` |

Every station module exposes `run(post_id, auto_approve=False)`. `run.py` walks
them in order.

## Beyond the four stations (full architecture)

These modules complete the reference architecture. All offline by default.

| Area | Module(s) | Reads -> Writes |
|---|---|---|
| Intelligence (front of funnel) | `engine/intelligence/intelligence.py` | `client-data/<client>/strategy.md` -> candidate seed dicts (no db write). Live SEO via DataForSEO when configured, offline stub otherwise. Reports path `live:dataforseo` vs `offline:stub`. |
| AEO (AI visibility) | `engine/aeo/aeo.py` | `client-data/<client>/positioning.md` + `strategy.md` -> `outputs/reports/<client>-aeo-visibility.md`. Is the brand cited in AI answers. Offline by default. |
| Integrations | `engine/integrations/dataforseo.py` | Credential-gated DataForSEO client (SEO + AEO), stdlib only. No network call without `DATAFORSEO_LOGIN` + `DATAFORSEO_PASSWORD`. |
| Feedback loop | `engine/feedback.py` | `analyzed` posts -> appends `client-data/<client>/learnings.md` |
| Dashboard | `engine/dashboard/metrics.py`, `report.py`, `notion_mirror.py` | whole pipeline -> summary dict, `outputs/reports/*.md`, `outputs/notion-mirror.json` |
| Ad creative | `engine/studio/render.py` `render_ad(post_id)` | post hook/body -> ad-sized PNG (wired into `ads_push`) |
| Leak guard (IP boundary) | `engine/leak_guard.py` | a client-data folder -> list of foreign client names |

Intelligence and feedback do not advance rows; they propose and learn. The
leak guard reads and reports only.

## The one human decision

`mission.gate` is the heart of the product: a human approves or rejects the post
before it publishes. `gate.py` has pure helpers (`approve`, `reject`,
`request_revision`, `approve_spend`) and a Flask app (`create_app()`, never
imported at module load) with a `/` content gate and a `/spend` ad spend gate.
For the unattended demo, `run.py` passes `auto_approve=True`.

## Skills (the craft)

In `.claude/skills/`. Skills inform, they do not execute.

- `intelligence`: how the analyst turns signals into grounded seed ideas.
- `content-os`: the five-step Brick chain (Intake, Topic, Angle, Hook, Story).
- `positioning-angles`: named angles and how to choose.
- `hook-library`: reusable first-line hook patterns (loaded by content-os Step 4).
- `story-structures`: reusable body arcs (loaded by content-os Step 5).
- `writing-style`: anti-AI-slop rules and self-check.
- `brand-test`: the 0 to 100 visual scoring rubric, 85 pass line.
- `publish-linkedin`: native LinkedIn formatting rules.
- `ad-copy`: compress a winning post into ad form, one CTA.
- `feedback-loop`: harvest winners back into the client learnings note.

## Commands (the loop)

In `.claude/commands/`. Commands orchestrate, loading the relevant skills.

- `/ai-cmo-intel [client]`: front of funnel, output candidate seed ideas. Live SEO path via DataForSEO activates when credentials are present.
- `/ai-cmo-aeo [client]`: AI visibility report to `outputs/reports/`. Offline by default, live with DataForSEO credentials.
- `/ai-cmo-generate "<seed>"`: `captured` -> `drafted`.
- `/ai-cmo-render <id>`: `drafted` -> `qc_review`.
- `/ai-cmo-publish <id>`: `approved` -> `published`.
- `/ai-cmo-engagement-sync <id>`: `published` -> `analyzed`.
- `/ai-cmo-ads <id>`: `analyzed` -> `ad_live`.
- `/ai-cmo-report`: aggregate the pipeline, write the weekly brief, mirror Notion.
- `/ai-cmo-onboard <slug>`: stand up a new client box (six layers + brand spec).

## Architecture docs

- `docs/architecture/multi-repo-model.md`: AIOS to AI CMO Core to per-client box,
  and the leak-guard rule (a client box contains no other client's name).
- `docs/architecture/agents.md`: the persona registry, mapping each
  marketing-department role to its skills, commands, and engine modules.

## Stub seams (offline by default)

| Env var | Real service |
|---|---|
| `AICMO_RENDER=playwright` | Studio browser render (post + ad creative) |
| `AICMO_VISION_QC=claude` | Vision brand QC |
| `ZERNIO_API_KEY` | Mission publish + analytics |
| `META_ACCESS_TOKEN` / `LINKEDIN_ACCESS_TOKEN` | Ads push campaign |
| `DATAFORSEO_LOGIN` + `DATAFORSEO_PASSWORD` | Intelligence live SEO + AEO visibility (both required). Pay-as-you-go, $50 min deposit, fractions of a cent per call. No live call without both. |
| `GSC_CREDENTIALS` / `APIFY_TOKEN` | Intelligence live GSC + competitor signals |
| `NOTION_TOKEN` | Notion board mirror (dashboard + human gate) |

None are required. The stubs are deterministic so tests and the demo are stable.

## Running and testing

```bash
python3 run.py "why your competitors all sound the same"   # full loop, prints transitions
python3 -m pytest -q                                       # all tests, db isolated to tmp_path
```

Tests isolate the DB with
`monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "t.db"))` then `db.init_db()`.

## House rules

- Never modify `db.py`.
- TDD: write the test first, watch it fail, implement, watch it pass.
- Keep `run.py` green after every change.
- No em dashes or hyphens as sentence breaks anywhere. Use commas or periods.
- No emojis. Show, do not claim. One idea per post.
- External services are stubbed so the loop never needs the network.
