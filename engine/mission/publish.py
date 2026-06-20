"""STATION 3, Mission: publish a scheduled post.

Reads:  status == scheduled   (uses image_path, hook, body, platform)
Writes: status == published   (sets published_url)

Signature: run(post_id: str, auto_approve: bool = False) -> None

Calls the Zernio client (engine/mission/zernio.py) which is a stub by default and
a real API call when ZERNIO_API_KEY is set. Records the returned live URL.

Platform formatting rules live in .claude/skills/publish-linkedin/SKILL.md and
are applied during drafting, not here. This module only ships the finished post.
"""

from db import Status, get_post, advance
from engine.mission import zernio


def run(post_id: str, auto_approve: bool = False) -> None:
    post = get_post(post_id)
    result = zernio.publish_post(
        image_path=post.get("image_path"),
        hook=post.get("hook"),
        body=post.get("body"),
        platform=post.get("platform", "linkedin"),
    )
    published_url = result["url"]
    print(f"    [publish] {result['mode']} posted to {post['platform']}: {published_url}")
    advance(post_id, Status.PUBLISHED, published_url=published_url)
