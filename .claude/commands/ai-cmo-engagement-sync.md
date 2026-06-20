---
description: MISSION CONTROL station. For a published post, verify it is live, then pull engagement metrics. Walks published -> analyzed so the Ads station has data to decide on.
---

# /ai-cmo-engagement-sync

Take a `published` post, confirm it went live, and pull its numbers. This closes the measurement loop.

**Argument:** the post id of a `published` record. Example: `/ai-cmo-engagement-sync 09c04e88242e411b8000ca531903ef17`

**Client:** `lumen-skin`.

## What to do

1. **Confirm the post is published.** The record must be at status `published` with a `published_url`. If not, stop and report the current status.

2. **Verify it is live.** Run from the repo root:

```bash
python3 -c "from engine.mission import publish_check; publish_check.run('<post_id>')"
```

This checks the URL and logs LIVE or NOT LIVE. It does not change the status. In stub mode (no `ZERNIO_API_KEY`) it assumes live.

3. **Pull analytics.** Run:

```bash
python3 -c "from engine.mission import analytics; analytics.run('<post_id>')"
```

This writes engagement into `metrics_json` and advances to `analyzed`. Default mode writes deterministic mock metrics. Real mode (key set) polls the platform analytics API.

4. **Report back** the live state and the metrics: likes, comments, shares, follows, impressions.

## Rules

- Write ONLY this field: metrics_json (analytics). publish_check writes nothing on the row.
- Run publish_check before analytics. A post that is not live should be flagged, not measured.
- Do not modify `db.py` or any other station's files.
- No em dashes or hyphens as breaks. No emojis.
