---
description: ONBOARDING. Turn a new client into the six markdown context layers plus a visual brand spec, so the AI CMO can write and design on brand for them. Produces a client box under client-data/<slug>/.
---

# /ai-cmo-onboard

Stand up a new client. A client becomes a box of markdown: the six context layers plus a brand spec. Once the box exists, every station works for that client with zero code changes.

**Argument:** the new client slug, lowercase with hyphens. Example: `/ai-cmo-onboard darko-wines`

## The six-layer contract

Every client box lives at `client-data/<slug>/` and holds exactly these files. `lumen-skin` is the worked example. Copy its shape, never its content.

1. `positioning.md`: what the brand stands for and the angle it owns.
2. `brand-and-audience.md`: who the audience is and what turns them off.
3. `strategy.md`: the content pillars and the cadence. The intelligence sweep and the Brick chain both read this.
4. `offers.md`: what the brand sells and the path to the sale.
5. `voice.md`: how the brand sounds, with concrete dos and don'ts.
6. `guardrails.md`: the hard nos. Claims the brand cannot make, words it never uses.

Plus the visual layer:
- `visual-brand.md`: exact colors, fonts, and the never-list the renderer reads.
- `brand.css`: the variables the post template uses.

## What to do

1. **Interview or intake.** Gather the brand facts. Do not invent them. If a fact is missing, ask for it.

2. **Create the box.** Make `client-data/<slug>/` and write all eight files above. Ground every claim in something the client actually said or published.

3. **Run the leak guard.** A client box must contain no other client's name. From the repo root:

```bash
python3 engine/leak_guard.py client-data/<slug> --clients <slug> lumen-skin <any other client slugs>
```

It must print CLEAN. If it reports a leak, remove the foreign name before going further.

4. **Smoke test the box.** Run the intelligence sweep, then one draft:

```bash
python3 engine/intelligence/intelligence.py --client <slug>
```

Confirm it returns candidate seeds grounded in the new strategy pillars.

5. **Report back** the path to the new box and the eight files written, plus the leak-guard result.

## Rules

- One box per client. No shared files between clients. The boundary is the product.
- The leak guard must pass before the box is considered onboarded.
- No em dashes or hyphens as breaks. No emojis. Show, do not claim.
