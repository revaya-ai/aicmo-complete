"""FEEDBACK LOOP — harvest winners back into strategy.

Every correction and every winner sharpens the next draft. This module closes
the loop: it reads the `analyzed` posts, ranks them by engagement, and appends a
learnings note (what won and the language that won) to
client-data/<client>/learnings.md. The Brain station reads that file next time so
the system gets better at this client's voice every cycle.

Reads:  status == analyzed   (uses metrics_json, hook, pillar, angle)
Writes: client-data/<client>/learnings.md   (append only)

It does NOT advance any post. It only learns from posts that have already been
measured. Offline, stdlib only. Metrics are the mock metrics from analytics.py.

Signature: run_for_client(client) -> int   (number of winners harvested)
"""

import json
import os
from datetime import datetime

import db
from engine.ads.ads_agent import engagement_rate

# How many top performers to write into the learnings note each run.
TOP_N = 3


def _learnings_path(client: str) -> str:
    return os.path.join(
        os.path.dirname(__file__), "..", "client-data", client, "learnings.md"
    )


def harvest_winners(posts: list) -> list:
    """Rank analyzed posts by engagement rate, highest first."""
    def rate(p):
        return engagement_rate(json.loads(p.get("metrics_json") or "{}"))

    return sorted(posts, key=rate, reverse=True)


def _format_note(client: str, winners: list) -> str:
    """Render one append-only learnings block for the top winners."""
    stamp = datetime.utcnow().strftime("%Y-%m-%d")
    lines = [f"\n## {stamp} feedback harvest ({client})\n"]
    for i, p in enumerate(winners, start=1):
        m = json.loads(p.get("metrics_json") or "{}")
        rate = engagement_rate(m)
        lines.append(f"### {i}. {p.get('hook', '(no hook)')}")
        lines.append(f"- What won: engagement rate {rate:.3f}.")
        lines.append(
            f"- Numbers: {m.get('likes', 0)} likes, {m.get('comments', 0)} comments, "
            f"{m.get('shares', 0)} shares, {m.get('follows', 0)} follows on "
            f"{m.get('impressions', 0)} impressions."
        )
        if p.get("pillar"):
            lines.append(f"- Pillar that worked: {p['pillar']}.")
        if p.get("angle"):
            lines.append(f"- Angle that worked: {p['angle']}.")
        lines.append(
            "- The language to reuse: the hook above opened a gap the reader "
            "needed closed. Borrow the structure, not the exact words."
        )
        lines.append("")
    return "\n".join(lines)


def run_for_client(client: str = "lumen-skin") -> int:
    """Harvest the top analyzed posts for a client and append a learnings note.

    Returns the number of winners written. Safe with zero analyzed posts.
    """
    analyzed = [p for p in db.list_by_status(db.Status.ANALYZED) if p.get("client") == client]
    if not analyzed:
        return 0

    winners = harvest_winners(analyzed)[:TOP_N]
    note = _format_note(client, winners)

    path = _learnings_path(client)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    header_needed = not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as fh:
        if header_needed:
            fh.write(f"# Learnings — {client}\n\nWhat won, harvested by the feedback loop.\n")
        fh.write(note)
    return len(winners)


def run(post_id: str = None, auto_approve: bool = False) -> None:
    """Pipeline-convention entry point. Harvests the demo client's winners.

    Kept signature-compatible with the station modules. post_id is ignored
    because the feedback loop works across all analyzed posts, not one row.
    """
    run_for_client("lumen-skin")


def main():
    import argparse

    p = argparse.ArgumentParser(description="Harvest winners into a client learnings note.")
    p.add_argument("--client", default="lumen-skin")
    a = p.parse_args()
    n = run_for_client(a.client)
    print(f"Harvested {n} winner(s) into {_learnings_path(a.client)}")


if __name__ == "__main__":
    main()
