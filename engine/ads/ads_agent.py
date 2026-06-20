"""STATION 4 — Ads (recommend-only): turn a winning post into a paid ad.

Reads:  status == analyzed   (uses metrics_json)
Writes: status == ad_recommended   if the post is a winner
            (sets ad_target_post_id, ad_budget, ad_audience, ad_status)
        then, after a HUMAN spend gate:
        status == ad_approved        (sets ad_spend_approved_by)
        status == ad_live            (ad pushed to the ad platform)

If the post is NOT a winner, this station does nothing and leaves it at
analyzed (the loop ends there).

Signature: run(post_id: str, auto_approve: bool = False) -> None

This station NEVER spends money on its own. It recommends. A human approves the
spend. For the demo, auto_approve=True approves the spend automatically.

The real version reads engagement, decides if it beats a winner threshold,
proposes budget + audience, then (after human approval) creates the campaign on
Meta / LinkedIn Ads. The stub recommends only if mock follows > FOLLOW_THRESHOLD,
auto-approves spend in run.py, and fakes ad_live.
"""

import json

from db import Status, get_post, advance, update_post

FOLLOW_THRESHOLD = 10


def run(post_id: str, auto_approve: bool = False) -> None:
    post = get_post(post_id)
    metrics = json.loads(post.get("metrics_json") or "{}")
    follows = metrics.get("follows", 0)

    # --- Decide: is this a winner worth promoting? -----------------------
    # TODO(builder): replace the single-metric check with a real winner score
    # (engagement rate, follows-per-impression, topic fit, etc).
    if follows <= FOLLOW_THRESHOLD:
        print(
            f"    [ads] follows={follows} <= {FOLLOW_THRESHOLD}: not a winner, "
            "no ad recommended."
        )
        return

    # --- Recommend (no spend yet) ----------------------------------------
    # TODO(builder): derive budget + audience from the brand + performance.
    advance(
        post_id,
        Status.AD_RECOMMENDED,
        ad_target_post_id=post_id,
        ad_budget=50.0,
        ad_audience="Women 25-45, skincare-curious, US/CA",
        ad_status="recommended",
    )
    print(
        f"    [ads] follows={follows} > {FOLLOW_THRESHOLD}: recommended "
        "$50/audience women 25-45."
    )

    # --- HUMAN spend gate ------------------------------------------------
    if not auto_approve:
        # TODO(builder): in production, stop here and wait for a human to
        # approve the spend (e.g. via the Flask gate). Do not spend money.
        print("    [ads] awaiting human spend approval. Stopping at ad_recommended.")
        return

    advance(post_id, Status.AD_APPROVED, ad_spend_approved_by="AUTO (demo loop)")

    # --- Go live ---------------------------------------------------------
    # TODO(builder): create the real campaign via Meta/LinkedIn Ads API and
    # store the campaign id in ad_status.
    update_post(post_id, ad_status="live:fake-campaign-123")
    advance(post_id, Status.AD_LIVE)
    print("    [ads] STUB campaign live: fake-campaign-123")
