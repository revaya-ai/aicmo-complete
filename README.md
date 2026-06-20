# aicmo-core

**The AI CMO.** A content marketing department that runs as software.

One content idea ("a post") is a single database row that walks through a status
pipeline. Each station reads the row at one status, does its job, and advances it
to the next. Every station now runs real logic against the frozen contract.

The whole loop runs OFFLINE on the Python standard library with no API keys. All
external services (image render, publishing, analytics, ad platforms) have stubs
that activate by default and only call the real service when the matching env var
is set. So a fresh clone walks a seed idea from `captured` all the way to
`ad_live` with one command and no setup.

## Who this is for (ICP)
A small business with a marketing team of one, or a founder who can't afford a
marketing team at all. The AI CMO runs the content department for them: ideates,
designs, gets human sign-off, publishes, measures, and recommends paid promotion
on the winners.

Demo client: **Lumen Skin Studio**, a small-batch skincare brand
(`client-data/lumen-skin/`).

## The contract-first rule
`db.py` is the **frozen contract**. It defines the `posts` table, the `Status`
constants, and the helper functions every station uses. Changing it requires
**all three builders to agree**. A schema change breaks everyone at once.
Everything else (the station internals) is yours to rewrite freely.

## The status pipeline

```
captured                          (a seed idea lands)
   |  brain.generate
drafted                           (pillar, angle, hook, body written)
   |  studio.render               (image_path set)
   |  studio.brand_qc
qc_review                         (passed visual QC, awaiting human)
   |  mission.gate  [HUMAN]
approved        (or rejected / needs_revision off-ramp)
   |  mission.schedule
scheduled
   |  mission.publish
published
   |  mission.analytics
analyzed                          (metrics in)
   |  ads.ads_agent               (only if it's a winner)
ad_recommended
   |  [HUMAN spend gate]
ad_approved
   |  ads.ads_agent
ad_live
```

Off-ramps: `needs_revision` and `rejected` (set at the human gate or by QC).

## The 4 stations (who owns what)

| Station | Folder | Reads -> Writes | Owner |
|---|---|---|---|
| 1. Brain | `engine/brain/` | `captured` -> `drafted` (Intake→Topic→Angle→Hook→Story brick chain) | Builder A |
| 2. Studio | `engine/studio/` | `drafted` -> image -> `qc_review` / `needs_revision` (HTML→PNG render + vision QC ≥85) | Builder B |
| 3. Mission | `engine/mission/` | `qc_review` -> `approved` -> `scheduled` -> `published` -> `analyzed` (human gate + publish + analytics) | Builder C |
| 4. Ads | `engine/ads/` | `analyzed` -> `ad_recommended` -> `ad_approved` -> `ad_live` (recommend-only, human spend gate) | Builder C |

## How to run the full loop

No installs needed. Standard library only.

```bash
python3 run.py "why your competitors all sound the same"
```

This creates a post, walks it through every station, prints each status
transition, and prints the final row as JSON. A real PNG render lands in
`renders/<post_id>.png` at 1080x1350. The post ends at `ad_live` if it is a
winner, or `analyzed` if its engagement does not clear the promote threshold.

The human gate and the ad spend gate auto-approve in `run.py` (via
`auto_approve=True`) so the demo completes unattended. In production a human acts
through the Flask gate (`python3 engine/mission/gate.py`, then the `/` page for
content and the `/spend` page for ad spend).

## Run the tests

```bash
python3 -m pytest -q
```

Every Python module has a test. Tests isolate the database with
`monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "t.db"))` then `db.init_db()`.
No test needs the network or an API key.

## The commands (Claude Code skills + commands)

The craft lives in skills, the loop runs through commands. Each command takes a
post id (except generate, which takes a seed idea) and walks the post forward.

| Command | Walks | Skills loaded |
|---|---|---|
| `/ai-cmo-generate "<seed>"` | `captured` -> `drafted` | content-os, positioning-angles, writing-style |
| `/ai-cmo-render <id>` | `drafted` -> `qc_review` | brand-test |
| `/ai-cmo-publish <id>` | `approved` -> `published` | publish-linkedin |
| `/ai-cmo-engagement-sync <id>` | `published` -> `analyzed` | (none) |
| `/ai-cmo-ads <id>` | `analyzed` -> `ad_live` | ad-copy |

The one human decision lives between render and publish: `mission.gate`.

## Going real (optional)

Each stub upgrades to the real service by setting one env var. The loop never
needs any of these.

| Env var | Turns on |
|---|---|
| `AICMO_RENDER=playwright` | Studio renders the HTML in a real browser |
| `AICMO_VISION_QC=claude` | Brand QC scores the image with a vision model |
| `ZERNIO_API_KEY` | Mission publishes and pulls analytics for real |
| `META_ACCESS_TOKEN` or `LINKEDIN_ACCESS_TOKEN` | Ads push creates a real campaign |

## For builders

1. Read `db.py`. That is the contract. **Do not change it** without the other
   two builders agreeing.
2. Open your station file. The docstring tells you exactly which status you read,
   which status you write, and the function signature.
3. Find the `# TODO(builder):` markers. Replace the stub logic there with real
   logic. Keep the same read/write statuses and the same `run(post_id,
   auto_approve=False)` signature.
4. Run `python run.py "..."` after every change. The loop must stay green.

Real builds will need the deps in `requirements.txt` and the keys in
`.env.example` (copy it to `.env`). The stub loop needs neither.

## Layout

```
db.py            # FROZEN CONTRACT (schema + helpers)
run.py           # orchestrator, walks one idea through every station
client-data/     # 6-layer context per client (lumen-skin demo)
templates/       # social post template (Station 2 renders this)
engine/          # the 4 stations
.claude/skills/  # the craft: content-os, brand-test, publish-linkedin, ad-copy, etc.
.claude/commands/ # the loop: ai-cmo-generate, render, publish, engagement-sync, ads
tests/           # pytest, one test file per module, db isolated to tmp_path
renders/         # generated PNGs (gitignored)
data/            # aicmo.db created here (gitignored)
```

For the architecture, the frozen contract, and the skills plus commands map, see
`CLAUDE.md`.
