"""STATION 3, Mission: schedule an approved post.

Reads:  status == approved
Writes: status == scheduled   (sets scheduled_for, an ISO timestamp)

Signature: run(post_id: str, auto_approve: bool = False) -> None

Picks the next weekday 09:00 slot in the future. A production version would read
the client's posting cadence and a best-time-to-post heuristic from past
engagement, but the next-weekday-morning rule is a sane, testable default.
"""

from datetime import datetime, timedelta

from db import Status, advance

POST_HOUR = 9  # 09:00 local, a calm morning slot


def next_slot(now: datetime) -> datetime:
    """Return the next weekday at POST_HOUR strictly after now.

    Pure and deterministic so it is easy to test. Skips Saturday and Sunday.
    """
    candidate = now.replace(hour=POST_HOUR, minute=0, second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=1)
    while candidate.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        candidate += timedelta(days=1)
    return candidate


def run(post_id: str, auto_approve: bool = False) -> None:
    scheduled_for = next_slot(datetime.utcnow()).isoformat()
    advance(post_id, Status.SCHEDULED, scheduled_for=scheduled_for)
