"""DASHBOARD: render a simple weekly brief (markdown).

Reads:  the metrics summary from engine/dashboard/metrics.py.
Writes: a markdown brief to outputs/reports/ (or a path you pass).

Offline, stdlib only. The brief is the artifact a client reads on Monday: what
the pipeline did, what won, and what it cost. No em dashes or hyphens as breaks.
"""

import os
from datetime import datetime

from engine.dashboard import metrics

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "outputs", "reports")


def render_markdown(summary: dict = None) -> str:
    """Render the weekly brief markdown from a metrics summary."""
    if summary is None:
        summary = metrics.summarize()
    stamp = datetime.utcnow().strftime("%Y-%m-%d")

    lines = [
        f"# Weekly brief, {stamp}",
        "",
        f"Total posts in the pipeline: {summary['total_posts']}.",
        f"Estimated run cost: ${summary['run_cost_usd']}.",
        "",
        "## Pipeline by stage",
        "",
    ]
    if summary["counts_by_status"]:
        for status in db_status_order(summary["counts_by_status"]):
            count = summary["counts_by_status"][status]
            lines.append(f"- {status}: {count}")
    else:
        lines.append("- Nothing in the pipeline yet.")

    lines += ["", "## What won", ""]
    if summary["top_posts"]:
        for i, p in enumerate(summary["top_posts"], start=1):
            lines.append(
                f"{i}. {p['hook'] or '(no hook)'} "
                f"(engagement rate {p['engagement_rate']}, status {p['status']})"
            )
    else:
        lines.append("No measured posts yet. Publish and sync analytics first.")

    lines += [
        "",
        "## Next move",
        "",
        "Feed the winners back into strategy with the feedback loop, then run the "
        "intelligence sweep for next week's seeds.",
        "",
    ]
    return "\n".join(lines)


def db_status_order(counts: dict) -> list:
    """Order statuses by the pipeline order in db, keeping only present ones."""
    import db

    return [s for s in db.STATUSES if s in counts]


def write_report(path: str = None) -> str:
    """Write the weekly brief to disk. Returns the path written."""
    if path is None:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y-%m-%d")
        path = os.path.join(REPORTS_DIR, f"weekly-brief-{stamp}.md")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render_markdown())
    return path


def main():
    print(f"Wrote {write_report()}")


if __name__ == "__main__":
    main()
