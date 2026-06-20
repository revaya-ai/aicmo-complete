---
description: MISSION CONTROL station. Take an approved post, schedule it for the next weekday morning, then publish it through Zernio. Walks approved -> scheduled -> published.
---

# /ai-cmo-publish

Take an `approved` post and ship it. This is the second half of Mission Control: pick a slot, then publish.

**Argument:** the post id of an `approved` record. Example: `/ai-cmo-publish 09c04e88242e411b8000ca531903ef17`

**Client:** `lumen-skin`. **Platform:** LinkedIn.

## What to do

1. **Load the craft.** Read and follow `publish-linkedin` (the LinkedIn format rules). Apply them as the final formatting pass on the body before it ships. Format only, never change the idea or voice.

2. **Confirm the post is ready.** The record must be at status `approved`. If not, stop and report the current status.

3. **Schedule it.** Run from the repo root:

```bash
python3 -c "from engine.mission import schedule; schedule.run('<post_id>')"
```

This sets `scheduled_for` to the next weekday 09:00 and advances to `scheduled`.

4. **Publish it.** Run:

```bash
python3 -c "from engine.mission import publish; publish.run('<post_id>')"
```

This calls the Zernio client and advances to `published` with the live URL. With no `ZERNIO_API_KEY` set it runs in stub mode and returns a fake URL, so the loop works offline. Set the key to publish for real.

5. **Report back** the `scheduled_for` slot, the `published_url`, and whether it ran in stub or real mode.

## Rules

- Write ONLY these fields: scheduled_for (schedule), published_url (publish). Status moves automatically.
- The format pass touches spacing and structure, never the message.
- Do not modify `db.py` or any other station's files.
- No em dashes or hyphens as breaks. No emojis. No engagement-bait CTA.
