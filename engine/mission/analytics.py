"""STATION 3 — Mission: pull analytics on a published post.

Reads:  status == published   (uses published_url)
Writes: status == analyzed    (sets metrics_json)

Signature: run(post_id: str, auto_approve: bool = False) -> None

The real version polls the platform API for engagement after some hours and
stores it as JSON. The stub writes mock likes / comments / follows so the Ads
station has something to decide on.
"""

import json

from db import Status, advance


def run(post_id: str, auto_approve: bool = False) -> None:
    # TODO(builder): fetch real engagement for post["published_url"] from the
    # platform analytics API. Keep the same JSON shape so Ads keeps working.
    metrics = {
        "likes": 142,
        "comments": 23,
        "shares": 11,
        "follows": 18,
        "impressions": 4200,
    }
    advance(post_id, Status.ANALYZED, metrics_json=json.dumps(metrics))
