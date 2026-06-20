"""STATION 3 — Mission: publish a scheduled post.

Reads:  status == scheduled   (uses image_path, hook, body, platform)
Writes: status == published   (sets published_url)

Signature: run(post_id: str, auto_approve: bool = False) -> None

The real version pushes the post + image to Zernio (or the platform API) and
records the live URL. The stub logs and sets a fake published_url.
"""

from db import Status, get_post, advance


def run(post_id: str, auto_approve: bool = False) -> None:
    post = get_post(post_id)

    # TODO(builder): call the Zernio API with image_path, hook, body, platform.
    # Capture the real returned post URL.
    published_url = f"https://example.test/{post_id}"
    print(f"    [publish] STUB posted to {post['platform']}: {published_url}")

    advance(post_id, Status.PUBLISHED, published_url=published_url)
