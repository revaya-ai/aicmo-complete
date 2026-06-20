"""STATION 3, Mission: a thin Zernio client wrapper.

Zernio is the publishing service the AI CMO posts through. This module is the
only place that knows how to talk to it, so every other station stays clean.

Two modes:
- STUB (default): no ZERNIO_API_KEY set. Returns a deterministic fake post URL.
  The whole loop runs offline with no account.
- REAL: ZERNIO_API_KEY is set. Calls the live API. Kept behind the env check so
  the default path never needs a key or the network.

Nothing here imports a network library at module load. The real call imports
inside the function so the stub path has zero dependencies.
"""

import hashlib
import os

STUB_BASE = "https://zernio.test/p"


def _stub_url(seed: str) -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"{STUB_BASE}/{digest}"


def publish_post(image_path: str, hook: str, body: str, platform: str = "linkedin") -> dict:
    """Publish a post. Returns {"url": str, "mode": "stub"|"real"}.

    Real path only runs when ZERNIO_API_KEY is set. Otherwise a stable fake URL.
    """
    api_key = os.environ.get("ZERNIO_API_KEY")
    if not api_key:
        return {"url": _stub_url(hook + body), "mode": "stub"}

    # Real path. Imported lazily so the stub path needs no http client.
    import json
    import urllib.request

    payload = json.dumps(
        {"platform": platform, "text": f"{hook}\n\n{body}", "image_path": image_path}
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.zernio.com/v1/posts",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return {"url": data["url"], "mode": "real"}


def is_live(url: str) -> bool:
    """Verify a published URL is live. Stub assumes live; real does a HEAD check."""
    if not os.environ.get("ZERNIO_API_KEY"):
        return True
    import urllib.request

    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return 200 <= resp.status < 400
    except Exception:
        return False
