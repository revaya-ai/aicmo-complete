# Card 1 — BRAIN (Think + Write) — Design Spec

> Status: approved (Shannon, 2026-06-20). Station owner: Brain builder.
> Architecture: Claude Code skills + commands (the craft lives in skills, the loop runs through commands; scripts are the runtime).

---

## Purpose

Turn a typed seed idea into an on-brand drafted post, grounded in the client's brand, run through anti-AI-slop. The draft is the handoff to Card 2 (Studio).

## Scope (hackathon MVP)

In:
- Input is a human-typed seed idea string.
- One client (`lumen-skin` demo) and one platform (LinkedIn).
- The Brick chain reasoning + anti-AI-slop + angle selection.
- Writes a `drafted` record via the frozen `engine/db.py` contract.

Out (later, not today):
- Research / intelligence auto-generating ideas (the upstream "phase 0").
- Multi-platform formatting (IG, X).
- Image (Card 2 owns that).

## Components

### Skills (`.claude/skills/`) — original, written from Jen's public deck, not copies

1. **content-os** — the Brick chain. Five locked steps, each producing one artifact the next step depends on:
   - Intake: restate the seed idea in one line.
   - Topic: one-line topic + which content pillar it serves (from the client strategy).
   - Angle: pick a named angle (loads `positioning-angles`).
   - Hook: write the opening line (information-gap, 5-10 words on line 1).
   - Story/Shift: outline the body arc, then write it (loads `writing-style`).
   - Rule: never skip a step, never write the body before the hook is locked.

2. **writing-style** — anti-AI-slop enforcement. No em dashes or hyphens as breaks. Banned-phrase list. Show-don't-claim (every claim needs a number, name, or date). No generic openers. One idea per post. Mix sentence length.

3. **positioning-angles** — a small library of named angles mapped to the client's audience and offers, used by the Angle step to choose deliberately rather than defaulting to generic.

### Command (`.claude/commands/`)

- **ai-cmo-generate** — entry point. Reads the seed idea argument + the client's 6-layer context, runs the Brick chain (loading the three skills in order), then calls `engine/db.py` to write the finished draft at status `drafted`. Reports the record id and the locked artifacts.

### Client context (`client-data/lumen-skin/`)

The 6-layer context (positioning, brand-and-audience, strategy, offers, voice, guardrails) provides grounding. Already scaffolded; refined so the Brick chain has real material (pillars defined in strategy, audience defined for angle selection, voice rules for the writing step).

### Runtime (`engine/db.py`)

The frozen contract carries over unchanged. Brain only writes these fields: `pillar`, `angle`, `hook`, `body`, and advances `status` to `drafted`. It must not touch any other column or any other station's files.

## Data flow

```
seed idea (string)
  -> ai-cmo-generate command
       reads client-data/lumen-skin/*.md  (grounding)
       runs content-os Brick chain:
         Intake -> Topic(+pillar) -> Angle(positioning-angles) -> Hook -> Story/Shift(writing-style)
  -> engine/db.py: create/advance record -> status "drafted" (pillar, angle, hook, body set)
  -> handoff to Card 2 (Studio) which reads status "drafted"
```

## Contract (frozen — shared with Studio and Mission Control)

Brain writes: `pillar`, `angle`, `hook`, `body`, `status='drafted'`. No other fields. Any change to the shared record requires all three builders to agree.

## Error handling

- Missing client context file: fail loud with the exact missing path (do not invent brand facts).
- Empty or junk seed idea: ask for a real seed idea rather than fabricating one.
- A Brick step that can't ground a claim: leave the claim out (show-don't-claim), do not hallucinate a statistic.

## Verification (definition of done)

Run `ai-cmo-generate "why competitors all sound the same"` and confirm:
1. A `drafted` record exists with all four fields populated.
2. The body reads genuinely on-brand for Lumen Skin (a non-technical SMB skincare brand).
3. The body passes the anti-AI-slop check: no em dashes, no banned phrases, no generic opener, claims are grounded.
4. The hook line 1 is 5-10 words and opens an information gap.

## Note on repo transition

The first scaffold was Python-first with a `run.py` stub loop. Card 1 establishes the skills+commands shape for the Brain slice. `engine/db.py` (the contract) is reused as-is. The legacy Python `run.py` orchestrator and the other stations' stubs are left untouched here; Mission Control reconciles the orchestrator during the end-of-day integration window. Card 1 is run and demoed directly via the `ai-cmo-generate` command.
