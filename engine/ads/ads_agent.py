"""STATION 4, Ads (recommend-only): turn a winning post into a paid ad.

Reads:  status == analyzed   (uses metrics_json)
Writes: status == ad_recommended   if the post is a winner
            (sets ad_target_post_id, ad_budget, ad_audience, ad_status)
        then, after the HUMAN spend gate:
        status == ad_approved        (sets ad_spend_approved_by)
        status == ad_live            (ad pushed via engine/ads/ads_push.py)

If the post is NOT a winner, this station does nothing and leaves it at
analyzed (the loop ends there).

Signature: run(post_id: str, auto_approve: bool = False) -> None

This station NEVER spends money on its own. It recommends. A human approves the
spend through engine/mission/gate.py (approve_spend). For the unattended demo,
auto_approve=True approves the spend automatically and pushes the ad live.

Winner detection uses an engagement RATE, not a single raw metric, so a post
that is popular relative to its reach wins, and a post with high impressions but
no interaction does not. The threshold and budget logic live in pure functions
so both branches are testable offline.
"""

import json

from db import Status, get_post, advance
from engine.mission.gate import approve_spend
from engine.ads import ads_push

# A post wins if its engagement rate clears this. Engagement rate =
# (likes + comments + shares + follows) / impressions.
ENGAGEMENT_RATE_THRESHOLD = 0.03
DEFAULT_BUDGET = 50.0
DEFAULT_AUDIENCE = "Women 25-45, skincare-curious, US/CA"


def engagement_rate(metrics: dict) -> float:
    """Interactions per impression. 0.0 when there are no impressions."""
    impressions = metrics.get("impressions", 0) or 0
    if impressions <= 0:
        return 0.0
    interactions = (
        metrics.get("likes", 0)
        + metrics.get("comments", 0)
        + metrics.get("shares", 0)
        + metrics.get("follows", 0)
    )
    return interactions / impressions


def is_winner(metrics: dict) -> bool:
    """True if the post's engagement rate clears the promote threshold."""
    return engagement_rate(metrics) >= ENGAGEMENT_RATE_THRESHOLD


def recommend_budget(metrics: dict) -> float:
    """Scale the budget with engagement. A stronger post earns more spend."""
    rate = engagement_rate(metrics)
    # Base budget, plus a bump for every point of rate over the threshold.
    over = max(0.0, rate - ENGAGEMENT_RATE_THRESHOLD)
    return round(DEFAULT_BUDGET + over * 1000, 2)


def run(post_id: str, auto_approve: bool = False) -> None:
    post = get_post(post_id)
    metrics = json.loads(post.get("metrics_json") or "{}")
    rate = engagement_rate(metrics)

    # --- Decide: is this a winner worth promoting? -----------------------
    if not is_winner(metrics):
        print(
            f"    [ads] engagement rate {rate:.3f} < {ENGAGEMENT_RATE_THRESHOLD}: "
            "not a winner, no ad recommended."
        )
        return

    # --- Recommend (no spend yet) ----------------------------------------
    budget = recommend_budget(metrics)
    advance(
        post_id,
        Status.AD_RECOMMENDED,
        ad_target_post_id=post_id,
        ad_budget=budget,
        ad_audience=DEFAULT_AUDIENCE,
        ad_status="recommended",
    )
    print(
        f"    [ads] engagement rate {rate:.3f} >= {ENGAGEMENT_RATE_THRESHOLD}: "
        f"recommended ${budget} to {DEFAULT_AUDIENCE}."
    )

    # --- HUMAN spend gate ------------------------------------------------
    if not auto_approve:
        print("    [ads] awaiting human spend approval. Stopping at ad_recommended.")
        return

    approve_spend(post_id, approver="AUTO (demo loop)")

    # --- Go live ---------------------------------------------------------
    ads_push.run(post_id, auto_approve=auto_approve)
