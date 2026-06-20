"""STATION 2 — Studio: draft -> rendered image.

Reads:  status == drafted   (uses hook, body)
Writes: image_path          (status stays drafted; brand_qc moves it next)

Signature: run(post_id: str, auto_approve: bool = False) -> None

The real version renders templates/social/post.html.j2 with the post's hook
and body, then screenshots it with Playwright at 1080x1350 into renders/<id>.png.
The stub just sets image_path to that location without producing a real file,
so the loop runs without Playwright installed.
"""

from db import get_post, update_post


def run(post_id: str, auto_approve: bool = False) -> None:
    post = get_post(post_id)
    image_path = f"renders/{post_id}.png"

    # TODO(builder): render templates/social/post.html.j2 with Jinja2 using
    # post["hook"] and post["body"], then screenshot it with Playwright:
    #   - set viewport to 1080x1350
    #   - load the rendered HTML
    #   - page.screenshot(path=image_path)
    # Make sure the renders/ directory exists first.

    update_post(post_id, image_path=image_path)
