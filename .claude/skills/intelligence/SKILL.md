---
name: intelligence
description: How the analyst turns raw signals (SEO, GEO, AEO, trends, competitor moves) into a short list of candidate seed ideas, each grounded in a client strategy pillar, then hands them to the strategist. Loaded by the ai-cmo-intel command.
---

# intelligence

## Purpose

The front of the funnel. Before the Brain writes anything, someone has to decide what is worth writing about. The analyst reads the signals, filters out the noise, and produces a small list of candidate seed ideas. Each seed is one line, tagged with the pillar it serves. The strategist then picks which seeds become posts.

## Before you start

Read the client context first:
- `client-data/<client>/strategy.md` for the content pillars. Every seed must map to one.
- `client-data/<client>/brand-and-audience.md` for who you are talking to.
- `client-data/<client>/positioning.md` for the angle the brand owns.

## The signals (offline by default)

The runtime (`engine/intelligence/intelligence.py`) is offline on the standard library. It grounds candidate seeds in the strategy pillars. Real signal sources turn on only when their env var is set:

- **SEO** (DATAFORSEO_LOGIN): keywords the audience already searches.
- **GEO and AEO**: how the brand shows up in AI answers and local results. A gap here is a content idea.
- **GSC** (GSC_CREDENTIALS): queries the client already ranks for, where one more post would win the page.
- **Trends and competitor signals** (APIFY_TOKEN): what is moving this week, and what competitors keep repeating that the brand can answer better.

## How to turn a signal into a seed

1. Start from a real signal or, offline, a strategy pillar.
2. Restate it as one plain line a reader would care about, not a keyword string.
3. Map it to exactly one content pillar from `strategy.md`. If it fits no pillar, drop it.
4. Tag the source so a reviewer can trace where it came from.

## What good output looks like

A short list, three to eight candidates, covering at least two pillars so the strategist has range. Each item:
- `idea`: one line, plain language, reader-first.
- `pillar`: a real pillar name from the client strategy.
- `source`: where the signal came from.
- `signal`: a one-line note on why it is worth writing.

## Hand off

Pass the list to the strategist (the Brain station). The strategist picks one seed, then `ai-cmo-generate` runs the Brick chain on it. Intelligence never writes to the database and never advances a row. It only proposes.

## Rules

- Every seed maps to a real strategy pillar. No orphan ideas.
- One idea per seed. Do not bundle three topics into one line.
- No em dashes or hyphens as breaks. No emojis.
- Offline by default. Never require a key to produce candidates.
