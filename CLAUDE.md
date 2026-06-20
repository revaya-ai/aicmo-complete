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

## The one human decision

`mission.gate` is the heart of the product: a human approves or rejects the post
before it publishes. `gate.py` has pure helpers (`approve`, `reject`,
`request_revision`, `approve_spend`) and a Flask app (`create_app()`, never
imported at module load) with a `/` content gate and a `/spend` ad spend gate.
For the unattended demo, `run.py` passes `auto_approve=True`.

## Skills (the craft)

In `.claude/skills/`. Skills inform, they do not execute.

- `content-os`: the five-step Brick chain (Intake, Topic, Angle, Hook, Story).
- `positioning-angles`: named angles and how to choose.
- `writing-style`: anti-AI-slop rules and self-check.
- `brand-test`: the 0 to 100 visual scoring rubric, 85 pass line.
- `publish-linkedin`: native LinkedIn formatting rules.
- `ad-copy`: compress a winning post into ad form, one CTA.

## Commands (the loop)

In `.claude/commands/`. Commands orchestrate, loading the relevant skills.

- `/ai-cmo-generate "<seed>"`: `captured` -> `drafted`.
- `/ai-cmo-render <id>`: `drafted` -> `qc_review`.
- `/ai-cmo-publish <id>`: `approved` -> `published`.
- `/ai-cmo-engagement-sync <id>`: `published` -> `analyzed`.
- `/ai-cmo-ads <id>`: `analyzed` -> `ad_live`.

## Stub seams (offline by default)

| Env var | Real service |
|---|---|
| `AICMO_RENDER=playwright` | Studio browser render |
| `AICMO_VISION_QC=claude` | Vision brand QC |
| `ZERNIO_API_KEY` | Mission publish + analytics |
| `META_ACCESS_TOKEN` / `LINKEDIN_ACCESS_TOKEN` | Ads push campaign |

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
