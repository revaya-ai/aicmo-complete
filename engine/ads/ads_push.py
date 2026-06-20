"""STATION 4, Ads: push an approved ad live.

Reads:  status == ad_approved   (uses ad_budget, ad_audience, ad_target_post_id)
Writes: status == ad_live       (sets ad_status to the campaign id)

Signature: run(post_id: str, auto_approve: bool = False) -> None

Two modes:
- STUB (default): no ad-platform tokens set. Returns a deterministic fake
  campaign id and goes live offline. Ads auth must NEVER block the content loop,
  so the stub is the floor.
- REAL: META_ACCESS_TOKEN or LINKEDIN_ACCESS_TOKEN set. Creates the campaign via
  the platform Ads API. Kept behind the token check.
"""

import hashlib
import os

from db import Status, get_post, advance


def _stub_campaign_id(post_id: str) -> str:
    digest = hashlib.sha256(post_id.encode("utf-8")).hexdigest()[:10]
    return f"live:stub-campaign-{digest}"


def create_campaign(post: dict) -> str:
    """Create the ad campaign. Returns a campaign id string.

    Real platforms only when a token is set, otherwise a stable stub id.
    """
    has_meta = os.environ.get("META_ACCESS_TOKEN")
    has_linkedin = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    if not (has_meta or has_linkedin):
        return _stub_campaign_id(post["id"])

    # Real path. Imported lazily so the stub path needs no http client.
    import json
    import urllib.request

    if has_meta:
        endpoint = "https://graph.facebook.com/v19.0/act_/campaigns"
        token = has_meta
    else:
        endpoint = "https://api.linkedin.com/rest/adCampaigns"
        token = has_linkedin
    payload = json.dumps(
        {
            "name": f"AI CMO boost {post['id'][:8]}",
            "daily_budget": post.get("ad_budget"),
            "audience": post.get("ad_audience"),
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return f"live:{data.get('id', 'unknown')}"


def run(post_id: str, auto_approve: bool = False) -> None:
    post = get_post(post_id)
    if post["status"] != Status.AD_APPROVED:
        print(f"    [ads_push] post {post_id} is {post['status']}, not ad_approved. Skipping.")
        return
    campaign_id = create_campaign(post)
    advance(post_id, Status.AD_LIVE, ad_status=campaign_id)
    print(f"    [ads_push] campaign {campaign_id} (budget ${post.get('ad_budget')})")
