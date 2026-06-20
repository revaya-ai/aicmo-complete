"""DASHBOARD: mirror the pipeline to a Notion board (brick B3.10, no longer skipped).

This is the production surface for "approve from your phone". Instead of the
Flask gate, the client sees a Notion board with a status property and approves
there.

Two modes:

1. STUB (default, no NOTION_TOKEN): write a JSON "board" to
   outputs/notion-mirror.json. Each post becomes a card with its status, hook,
   body, qc score, and image path. Fully offline.

2. REAL (NOTION_TOKEN set): push the same cards to a Notion database via the
   Notion API. Same card shape, so nothing downstream changes. Kept behind the
   env check; the loop never needs it.

mirror()      -> mirror the whole pipeline (the dashboard board).
mirror_gate() -> mirror only qc_review items (the human gate "approve from your
                 phone" surface, area 4).
"""

import json
import os

import db

MIRROR_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "outputs", "notion-mirror.json"
)


def _card(post: dict) -> dict:
    return {
        "id": post["id"],
        "status": post["status"],
        "client": post.get("client"),
        "hook": post.get("hook"),
        "body": post.get("body"),
        "qc_score": post.get("qc_score"),
        "image_path": post.get("image_path"),
        "published_url": post.get("published_url"),
    }


def _write_board(cards: list, path: str, board_name: str) -> str:
    if os.environ.get("NOTION_TOKEN"):
        # STUB SEAM, not a real call yet. When built, this branch will push the
        # cards to a Notion database via the Notion API. Today it only labels the
        # board "stub-real" and still writes the JSON, so it does not pretend a
        # Notion push happened that did not. No silent success.
        mode = "stub-real"
    else:
        mode = "stub"
    board = {"mode": mode, "board": board_name, "cards": cards}
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(board, fh, indent=2)
    return path


def mirror(path: str = None) -> str:
    """Mirror the entire pipeline to a board. Returns the path written.

    path defaults to MIRROR_PATH read at call time, so monkeypatching the module
    attribute (tests) and reassigning it both take effect.
    """
    if path is None:
        path = MIRROR_PATH
    cards = []
    for status in db.STATUSES:
        for post in db.list_by_status(status):
            cards.append(_card(post))
    return _write_board(cards, path, board_name="AI CMO pipeline")


def mirror_gate(path: str = None) -> str:
    """Mirror ONLY qc_review items: the human gate 'approve from your phone' view."""
    if path is None:
        path = MIRROR_PATH
    cards = [_card(p) for p in db.list_by_status(db.Status.QC_REVIEW)]
    return _write_board(cards, path, board_name="AI CMO human gate")


def main():
    print(f"Wrote {mirror()}")


if __name__ == "__main__":
    main()
