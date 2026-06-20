"""STATION 3, Mission: pull analytics on a published post.

Reads:  status == published   (uses published_url)
Writes: status == analyzed    (sets metrics_json)

Signature: run(post_id: str, auto_approve: bool = False) -> None

The default path writes deterministic mock metrics derived from the post URL, so
the Ads station always has something to decide on and tests are stable. A real
path (ZERNIO_API_KEY set) would poll the platform analytics API and keep the same
JSON shape so Ads keeps working unchanged.
"""

import hashlib
import json
import os

from db import Status, get_post, advance


def mock_metrics(seed: str) -> dict:
    """Deterministic fake engagement derived from a seed string.

    Same seed gives the same numbers, so tests are stable and a winner is a
    winner every run. Numbers land in a realistic range for a small brand.
    """
    h = hashlib.sha256(seed.encode("utf-8")).digest()
    impressions = 2000 + h[0] * 20  # 2000 to ~7100
    likes = 40 + h[1] % 160  # 40 to 199
    comments = 5 + h[2] % 40  # 5 to 44
    shares = 1 + h[3] % 25  # 1 to 25
    follows = 2 + h[4] % 40  # 2 to 41
    return {
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "follows": follows,
        "impressions": impressions,
    }


def run(post_id: str, auto_approve: bool = False) -> None:
    post = get_post(post_id)
    if os.environ.get("ZERNIO_API_KEY"):
        # Real path would call zernio analytics here and shape the result the
        # same way mock_metrics does. Left as the upgrade seam.
        metrics = mock_metrics(post.get("published_url") or post_id)
    else:
        metrics = mock_metrics(post.get("published_url") or post_id)
    advance(post_id, Status.ANALYZED, metrics_json=json.dumps(metrics))
