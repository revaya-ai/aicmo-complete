"""MISSION CONTROL cron: nightly engagement sync.

sync_engagement(client) walks every post for the client that sits in published
or analyzed status, pulls its engagement metrics, and writes them back to the
row via the frozen db.py API. This is the scheduled cousin of the
ai-cmo-engagement-sync command, which syncs one post by id. This module syncs
the whole client at a fixed cadence so numbers stay fresh without a human in the
loop.

Cadence: nightly at 06:30 and 18:30. Engagement on a fresh post climbs fast in
the first hours, so a morning and an evening pull keep metrics current for the
Ads station and the dashboard. The schedule is reflected in the
ai-cmo-engagement-sync command file.

Two modes:
- OFFLINE (default): no analytics client injected. Writes deterministic mock
  metrics derived from the post URL, matching the analytics station shape, so
  the loop runs with zero keys and tests are stable. No network call.
- LIVE: a configured analytics client is injected. Its metrics are used instead.
  Kept behind the injection so the default path never needs a key or the network.

Writes ONLY metrics_json on each row, via db.update_post. It never changes a
post's status and never modifies db.py.
"""

import json

import db
from db import Status, list_by_status, update_post

# Cron cadence for the scheduled run. Used by the launchd / cron wiring and
# documented in the ai-cmo-engagement-sync command.
CADENCE = ["06:30", "18:30"]

# Statuses whose engagement is worth refreshing.
_SYNCABLE = [Status.PUBLISHED, Status.ANALYZED]


def offline_metrics(seed: str) -> dict:
    """Deterministic mock engagement derived from a seed string.

    Reuses the analytics station's mock_metrics so the shape and numbers match
    the rest of the pipeline. Same seed gives the same numbers, so tests are
    stable. Imported lazily so this module has no import-time coupling.
    """
    from engine.mission.analytics import mock_metrics

    return mock_metrics(seed)


def sync_engagement(client: str, analytics_client=None) -> dict:
    """Sync engagement for every published or analyzed post of one client.

    Returns {"client": str, "synced": int, "mode": "offline"|"live"}. Writes
    metrics_json on each matching row via the frozen db.py API. Offline by
    default, so no network call unless a configured analytics_client is injected.
    """
    live = analytics_client is not None and analytics_client.is_configured()
    mode = "live" if live else "offline"

    synced = 0
    for status in _SYNCABLE:
        for post in list_by_status(status):
            if post.get("client") != client:
                continue
            seed = post.get("published_url") or post["id"]
            if live:
                metrics = analytics_client.metrics_for(seed)
            else:
                metrics = offline_metrics(seed)
            update_post(post["id"], metrics_json=json.dumps(metrics))
            synced += 1

    return {"client": client, "synced": synced, "mode": mode}


def main() -> None:
    """Entry point for the scheduled run. Syncs the demo client offline."""
    db.init_db()
    result = sync_engagement("lumen-skin")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
