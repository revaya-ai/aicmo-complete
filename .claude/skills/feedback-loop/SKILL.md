---
name: feedback-loop
description: How the AI CMO learns from itself. Every correction and every winner sharpens the next draft. Harvest the top performing posts, name what won and the language that won, and write it back to the client learnings note so the Brain reuses it. Backed by engine/feedback.py.
---

# feedback-loop

## Purpose

A marketing department that never learns repeats its average. This loop turns measured results into reusable craft. It reads the posts that have already been measured, finds the winners, and writes down what made them win in plain language. The Brain station reads that note before the next draft, so the system gets sharper at this client every cycle.

## The rule

Every correction and every winner sharpens the next draft.

- A **winner** (high engagement) tells you the angle, pillar, and hook structure that landed. Reuse the structure.
- A **correction** (a human reject or revision note at the gate) tells you what to stop doing. Record it the same way.

## What to harvest

From the `analyzed` posts for the client:
1. Rank by engagement rate, not by raw likes. A post that is popular relative to its reach is the real winner.
2. Take the top performers.
3. For each, write down: the hook, the pillar that worked, the angle that worked, and the engagement numbers as proof.
4. Note the language to reuse. Borrow the structure of the winning hook, not the exact words.

## Where it goes

Append to `client-data/<client>/learnings.md`. Append only, never overwrite. Each run adds a dated block so the history of what works builds over time.

## How the Brain uses it

Before the next Brick chain, the Brain reads `learnings.md`. The winning angles and hook structures bias the next draft toward what already works for this audience. That is the loop closing.

## Rules

- Rank by engagement rate, never by a single raw metric.
- Append, do not overwrite. The history is the value.
- Plain language. Say what won and why, not a metrics dump.
- No em dashes or hyphens as breaks. No emojis.
