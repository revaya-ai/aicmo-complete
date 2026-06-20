"""STATION 3, Mission: pull analytics on a published post.

Reads:  status == published   (uses published_url)
Writes: status == analyzed    (sets metrics_json)

Signature: run(post_id: str, auto_approve: bool = False) -> None

The default path writes deterministic mock metrics derived from the post URL, so
the Ads station always has something to decide on and tests are stable.

When ZERNIO_API_KEY is set, real_metrics() is the seam for a live analytics pull.
It is currently a STUB that raises NotImplementedError: there is no real Zernio
call wired yet, so it falls back to mock metrics rather than pretending. The
docstring and code both say so plainly. The same JSON shape is returned either
way so Ads keeps working unchanged when the real call is built.
"""

import hashlib
import json
import os

from db import Status, get_post, advance


def real_metrics(published_url: str) -> dict:
    """STUB seam for a live Zernio analytics pull.

    Not implemented yet. When built, this will call the Zernio analytics API for
    published_url and return the same dict shape as mock_metrics(). Until then it
    raises so callers fall back to mock_metrics() instead of silently faking a
    real pull.
    """
    raise NotImplementedError(
        "real Zernio analytics not wired yet; using mock_metrics() fallback"
    )


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
    seed = post.get("published_url") or post_id
    if os.environ.get("ZERNIO_API_KEY"):
        # Real seam. real_metrics() is a stub that raises until the live Zernio
        # call is built, so we fall back to mock metrics rather than faking it.
        try:
            metrics = real_metrics(seed)
        except NotImplementedError:
            metrics = mock_metrics(seed)
    else:
        metrics = mock_metrics(seed)
    advance(post_id, Status.ANALYZED, metrics_json=json.dumps(metrics))
