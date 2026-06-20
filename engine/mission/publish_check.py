"""STATION 3, Mission: verify a published post is live.

Reads:  status == published   (uses published_url)
Writes: nothing on the row. Logs a verification check only.

Signature: run(post_id: str, auto_approve: bool = False) -> None

In production this runs on a cron every 30 minutes to catch a post that failed
to go live or was taken down. The stub assumes live (zernio.is_live returns True
without an API key). Status is never changed here; this is a watchdog, not a
pipeline step. The engagement-sync command runs this right before analytics.
"""

from db import Status, get_post
from engine.mission import zernio


def check(post_id: str) -> bool:
    """Return True if the post's published_url is live. Stub returns True."""
    post = get_post(post_id)
    url = post.get("published_url")
    if not url:
        return False
    return zernio.is_live(url)


def run(post_id: str, auto_approve: bool = False) -> None:
    post = get_post(post_id)
    if post["status"] != Status.PUBLISHED:
        print(f"    [publish_check] post {post_id} is {post['status']}, not published. Skipping.")
        return
    live = check(post_id)
    state = "LIVE" if live else "NOT LIVE"
    print(f"    [publish_check] {post.get('published_url')}: {state}")
