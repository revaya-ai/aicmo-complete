---
description: INTELLIGENCE station. Run the intelligence sweep for a client and output a short list of candidate seed ideas, each grounded in a strategy pillar, ready to feed the strategist.
---

# /ai-cmo-intel

Run the front-of-funnel sweep. Produce candidate seed ideas for the client so the Brain station has something grounded to write about.

**Argument:** the client slug. Default: `lumen-skin`. Example: `/ai-cmo-intel lumen-skin`

## What to do

1. **Load the craft.** Read and follow the `intelligence` skill.

2. **Load the client context.** Read `client-data/<client>/strategy.md`, `brand-and-audience.md`, and `positioning.md`. Do not invent brand facts.

3. **Run the sweep.** From the repo root:

```bash
python3 engine/intelligence/intelligence.py --client lumen-skin
```

This prints the candidate seeds as JSON, prefixed by which path ran:

- `offline:stub` means no DataForSEO credentials, so seeds are grounded in the strategy pillars only.
- `live:dataforseo` means `DATAFORSEO_LOGIN` and `DATAFORSEO_PASSWORD` are both set, so seeds come from real keyword demand via DataForSEO Labs, still mapped to the client pillars.

The live SEO path activates only when both credentials are present. With no credentials, or on any client error, the sweep falls back to the deterministic offline seeds. No live call is ever made without credentials. See `/ai-cmo-aeo` for the AEO visibility report that uses the same account.

4. **Review and shortlist.** Read the candidates. Apply the `intelligence` skill filters: one idea per seed, every seed mapped to a real pillar, at least two pillars covered. Drop anything that fits no pillar or duplicates another.

5. **Report back** the shortlist as a short table: idea, pillar, source, why it is worth writing. Recommend one seed to send to `/ai-cmo-generate` next.

## Rules

- Intelligence never writes to `db.py` and never advances a row. It proposes only.
- Do not modify `db.py` or any station file.
- No em dashes or hyphens as breaks. No emojis. One idea per seed.
