---
name: ad-copy
description: Turn a winning organic post into ad-format copy. Shorter, sharper, one clear call to action. Loaded by the ai-cmo-ads command when a post is recommended for paid promotion. The organic post earned attention for free, the ad has to earn it with money, so the copy works harder.
---

# ad-copy

## Purpose

An organic post that won gets a second life as a paid ad. The job here is not to write something new. It is to compress the winning post into ad form: faster to the point, one promise, one action. A paid ad is interrupting someone, so it has to pay for that interruption immediately.

## Before you start

Read the winning post first:
- The post's `hook` and `body` from the row (it is at status analyzed or ad_recommended).
- `client-data/<client>/voice.md` so the ad still sounds like the brand.
- `client-data/<client>/offers.md` so the call to action points at a real offer.

## The rules

### Keep the winning hook idea
The organic hook already proved it stops the scroll. Keep its core idea. You may tighten it, but do not throw away the thing that worked.

### Cut to one promise
The organic body can teach three things. The ad makes one promise. Find the single most compelling line in the winning post and build the ad around it. Cut everything else.

### Shorter than organic
- Headline: under 8 words.
- Primary text: 2 to 4 short lines. No more.
- Every line earns its place or it goes.

### One call to action, and only one
- Name the next step in plain words: "Shop the routine", "Book a skin consult", "Get the guide".
- Point it at a real offer from offers.md. Never invent an offer.
- One CTA. Two CTAs is zero CTAs.

### Match the audience
The ad targets the recommended audience (ad_audience on the row). Speak to that person, not to everyone.

## Voice and bans

- Same brand voice as organic. Honest, warm, specific.
- No em dashes or hyphens as breaks. Use commas or periods.
- No emojis. No hype words. No fake urgency.
- Show, do not claim. A number or a specific beats an adjective.

## Output contract

Return three things for the ad:
- a headline, under 8 words.
- primary text, 2 to 4 short lines.
- one call to action that maps to a real offer.

These feed the ad creative and the campaign that ads_push sends live.
