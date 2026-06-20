"""DASHBOARD: aggregate the pipeline into a metrics summary.

Reads:  every row in the posts table (across all statuses).
Writes: nothing to db.py. Returns a plain dict the report and the Notion mirror
        render. Offline, stdlib only.

The summary answers the questions a client asks: how many posts at each stage,
which ones are winning, and what the run cost. Cost is a stub (the real version
would sum token spend per run); it is deterministic so tests are stable.
"""

import json

import db
from engine.ads.ads_agent import engagement_rate

# Stub per-post pipeline cost in USD. The real version sums token + render +
# publish cost per run. Deterministic so the dashboard is stable offline.
STUB_COST_PER_POST = 0.12


def _all_posts() -> list:
    posts = []
    for status in db.STATUSES:
        posts.extend(db.list_by_status(status))
    return posts


def summarize() -> dict:
    """Aggregate the whole pipeline into one summary dict."""
    posts = _all_posts()

    counts = {}
    for p in posts:
        counts[p["status"]] = counts.get(p["status"], 0) + 1

    # Top posts by engagement rate among anything that has metrics.
    measured = [p for p in posts if p.get("metrics_json")]

    def rate(p):
        return engagement_rate(json.loads(p.get("metrics_json") or "{}"))

    top = sorted(measured, key=rate, reverse=True)[:5]
    top_posts = [
        {
            "id": p["id"],
            "hook": p.get("hook"),
            "status": p["status"],
            "engagement_rate": round(rate(p), 4),
        }
        for p in top
    ]

    return {
        "total_posts": len(posts),
        "counts_by_status": counts,
        "top_posts": top_posts,
        "run_cost_usd": round(len(posts) * STUB_COST_PER_POST, 2),
    }


def main():
    print(json.dumps(summarize(), indent=2))


if __name__ == "__main__":
    main()
