---
description: AEO station. Build an AI visibility report for a client. For the client's target questions and keywords, check whether the brand is cited in AI answers and what the AI search volume looks like. Offline by default, live when DataForSEO credentials are set.
---

# /ai-cmo-aeo

Run the Answer Engine Optimization sweep. Produce an AI visibility report so the client can see where AI answers cite them and where they do not. Each uncited query is a content gap worth writing about.

**Argument:** the client slug. Default: `lumen-skin`. Example: `/ai-cmo-aeo lumen-skin`

## What to do

1. **Load the client context.** Read `client-data/<client>/positioning.md` and `strategy.md`. The module pulls the target questions and keywords from these. Do not invent brand facts.

2. **Run the report.** From the repo root:

```bash
python3 engine/aeo/aeo.py --client lumen-skin
```

This writes the report to `outputs/reports/<client>-aeo-visibility.md` and prints which path ran:

- `offline:stub` means no DataForSEO credentials were set, so the report uses a deterministic offline mock. It still runs for anyone.
- `live:dataforseo` means `DATAFORSEO_LOGIN` and `DATAFORSEO_PASSWORD` were both set, so the report pulls real AI search volume and brand mention data.

3. **Read the report.** Open `outputs/reports/<client>-aeo-visibility.md`. Look at the summary (how many target queries cite the brand) and the per-query detail table.

4. **Report back** the highest-value gaps: the queries where the brand is not cited but the buyer intent is strong. Recommend a content seed for each, then hand off to `/ai-cmo-intel` and `/ai-cmo-generate` to write them.

## Going live

The report is offline by default. To pull real AI visibility data, set both credentials in the environment:

```
DATAFORSEO_LOGIN=...
DATAFORSEO_PASSWORD=...
```

DataForSEO is pay-as-you-go with a $50 minimum deposit. AI keyword data is about $0.0001 per keyword. No live call is ever made without both credentials present.

## Rules

- Offline by default. Never require a key to produce a report.
- The report always states its data source. No silent pretending a live call happened.
- Do not modify `db.py` or any station file.
- No em dashes or hyphens as breaks. No emojis.
