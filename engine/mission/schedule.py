"""STATION 3 — Mission: schedule an approved post.

Reads:  status == approved
Writes: status == scheduled   (sets scheduled_for, an ISO timestamp)

Signature: run(post_id: str, auto_approve: bool = False) -> None

The real version picks an optimal slot from the content calendar / posting
cadence. The stub just schedules it for "now + 1 hour".
"""

from datetime import datetime, timedelta

from db import Status, advance


def run(post_id: str, auto_approve: bool = False) -> None:
    # TODO(builder): choose a real slot using the client's calendar and the
    # best-time-to-post heuristic for the platform.
    scheduled_for = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    advance(post_id, Status.SCHEDULED, scheduled_for=scheduled_for)
