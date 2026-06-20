---
description: ADS station. Take an analyzed post, decide if it is a winner worth promoting, recommend a budget and audience, pass a human spend gate, then push the ad live. Walks analyzed -> ad_recommended -> ad_approved -> ad_live.
---

# /ai-cmo-ads

Take an `analyzed` post and, if it earned it, turn it into a live paid ad. This station recommends. A human approves the spend. It never spends money on its own.

**Argument:** the post id of an `analyzed` record. Example: `/ai-cmo-ads 09c04e88242e411b8000ca531903ef17`

**Client:** `lumen-skin`.

## What to do

1. **Load the craft.** Read and follow `ad-copy` (how to compress a winning post into ad form). Read the offers it points to:
   - `client-data/lumen-skin/offers.md`
   - `client-data/lumen-skin/voice.md`

2. **Confirm the post is ready.** The record must be at status `analyzed` with `metrics_json`. If not, stop and report the current status.

3. **Recommend or stop.** Run from the repo root:

```bash
python3 -c "from engine.ads import ads_agent; ads_agent.run('<post_id>', auto_approve=False)"
```

If the engagement rate clears the threshold, the post advances to `ad_recommended` with a budget and audience. If it does not, it stays `analyzed` and the loop ends here. Report which happened.

4. **Spend gate.** A human approves the spend. For the unattended demo this is automatic. To approve manually:

```bash
python3 -c "from engine.mission import gate; gate.approve_spend('<post_id>', approver='Shannon')"
```

This advances `ad_recommended` to `ad_approved`. In production the human clicks Approve on the `/spend` page of the Flask gate.

5. **Push it live.** Run:

```bash
python3 -c "from engine.ads import ads_push; ads_push.run('<post_id>')"
```

This advances `ad_approved` to `ad_live` and records the campaign id in `ad_status`. With no ad-platform tokens set it runs in stub mode and returns a fake campaign id, so the loop works offline.

6. **Report back** the engagement rate, the recommended budget and audience, who approved the spend, and the campaign id.

## Rules

- Write ONLY these fields: ad_target_post_id, ad_budget, ad_audience, ad_status (recommend), ad_spend_approved_by (spend gate), ad_status (push). Status moves automatically.
- Never spend money without a human spend approval. The gate is the point.
- Ads auth must never block the content loop. If tokens are missing, the stub still completes.
- Do not modify `db.py` or any other station's files.
- No em dashes or hyphens as breaks. No emojis. One CTA per ad, mapped to a real offer.
