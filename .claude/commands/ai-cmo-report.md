---
description: DASHBOARD station. Aggregate the whole pipeline into a metrics summary and write a weekly client brief to outputs/reports/. Optionally mirror the pipeline to a Notion board.
---

# /ai-cmo-report

Produce the weekly brief: what the pipeline did, what won, what it cost. This is the artifact the client reads on Monday.

**Argument:** none required. Runs for the whole pipeline.

## What to do

1. **Aggregate.** From the repo root:

```bash
python3 engine/dashboard/metrics.py
```

This prints the summary: counts by status, top posts by engagement, and the run cost (stub cost offline).

2. **Write the brief.** From the repo root:

```bash
python3 engine/dashboard/report.py
```

This writes `outputs/reports/weekly-brief-<date>.md`. Read it back and confirm it reflects the pipeline.

3. **Mirror to Notion (optional).** To put the board where a client can see it:

```bash
python3 engine/dashboard/notion_mirror.py
```

Offline this writes `outputs/notion-mirror.json` (mode "stub"). With `NOTION_TOKEN` set it pushes the same cards to a real Notion database.

4. **Report back** the path to the brief and a two line summary: how many posts moved this cycle and which post won.

## Rules

- The report reads the pipeline. It never advances a row or writes to `db.py`.
- Do not modify `db.py` or any station file.
- No em dashes or hyphens as breaks. No emojis.
