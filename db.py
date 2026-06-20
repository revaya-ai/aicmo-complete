"""THE FROZEN CONTRACT.

This module is the single shared contract for the entire AI CMO pipeline.
Every station imports from here. Do NOT change the schema, the Status values,
or the helper signatures without all three builders agreeing first.

A content "post" is a single row that walks through the status pipeline:

    captured -> drafted -> qc_review -> approved -> scheduled
             -> published -> analyzed -> ad_recommended -> ad_approved -> ad_live

(with needs_revision / rejected as off-ramps)

SQLite lives at data/aicmo.db. Rows come back as plain dicts.
"""

import os
import sqlite3
import uuid
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "aicmo.db")


class Status:
    """String constants for every status in the pipeline. Use these, not literals."""

    CAPTURED = "captured"
    DRAFTED = "drafted"
    QC_REVIEW = "qc_review"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ANALYZED = "analyzed"
    AD_RECOMMENDED = "ad_recommended"
    AD_APPROVED = "ad_approved"
    AD_LIVE = "ad_live"


# Canonical ordered list. Validation uses this.
STATUSES = [
    Status.CAPTURED,
    Status.DRAFTED,
    Status.QC_REVIEW,
    Status.NEEDS_REVISION,
    Status.REJECTED,
    Status.APPROVED,
    Status.SCHEDULED,
    Status.PUBLISHED,
    Status.ANALYZED,
    Status.AD_RECOMMENDED,
    Status.AD_APPROVED,
    Status.AD_LIVE,
]

# The complete set of columns on the posts table. update_post validates against this.
COLUMNS = [
    "id",
    "client",
    "seed_idea",
    "pillar",
    "angle",
    "hook",
    "body",
    "platform",
    "image_path",
    "qc_score",
    "qc_notes",
    "status",
    "scheduled_for",
    "published_url",
    "metrics_json",
    "human_note",
    "ad_target_post_id",
    "ad_budget",
    "ad_audience",
    "ad_status",
    "ad_spend_approved_by",
    "created_at",
    "updated_at",
]

# Columns a caller is allowed to set via update_post (everything except the PK).
_WRITABLE = set(COLUMNS) - {"id"}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> str:
    return datetime.utcnow().isoformat()


def init_db() -> None:
    """Create the posts table if it does not already exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id                    TEXT PRIMARY KEY,
                client                TEXT,
                seed_idea             TEXT,
                pillar                TEXT,
                angle                 TEXT,
                hook                  TEXT,
                body                  TEXT,
                platform              TEXT DEFAULT 'linkedin',
                image_path            TEXT,
                qc_score              INTEGER,
                qc_notes              TEXT,
                status                TEXT,
                scheduled_for         TEXT,
                published_url         TEXT,
                metrics_json          TEXT,
                human_note            TEXT,
                ad_target_post_id     TEXT,
                ad_budget             REAL,
                ad_audience           TEXT,
                ad_status             TEXT,
                ad_spend_approved_by  TEXT,
                created_at            TEXT,
                updated_at            TEXT
            )
            """
        )
        conn.commit()


def create_post(client: str, seed_idea: str, platform: str = "linkedin") -> str:
    """Insert a new post at status 'captured'. Returns the new post id."""
    post_id = uuid.uuid4().hex
    now = _now()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO posts (id, client, seed_idea, platform, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (post_id, client, seed_idea, platform, Status.CAPTURED, now, now),
        )
        conn.commit()
    return post_id


def get_post(post_id: str):
    """Return a post as a dict, or None if it does not exist."""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    return dict(row) if row else None


def update_post(post_id: str, **fields) -> None:
    """Update the given columns on a post. Always bumps updated_at.

    Raises ValueError on any unknown column name so a typo surfaces immediately.
    """
    if not fields:
        return
    unknown = set(fields) - _WRITABLE
    if unknown:
        raise ValueError(
            f"update_post got unknown column(s): {sorted(unknown)}. "
            f"Writable columns: {sorted(_WRITABLE)}"
        )
    fields["updated_at"] = _now()
    assignments = ", ".join(f"{col} = ?" for col in fields)
    values = list(fields.values()) + [post_id]
    with _connect() as conn:
        conn.execute(f"UPDATE posts SET {assignments} WHERE id = ?", values)
        conn.commit()


def list_by_status(status: str) -> list:
    """Return all posts at a given status, as a list of dicts."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM posts WHERE status = ? ORDER BY created_at", (status,)
        ).fetchall()
    return [dict(r) for r in rows]


def advance(post_id: str, new_status: str, **fields) -> None:
    """Move a post to new_status (validated against STATUSES) plus any extra fields."""
    if new_status not in STATUSES:
        raise ValueError(
            f"advance got invalid status {new_status!r}. Valid: {STATUSES}"
        )
    fields["status"] = new_status
    update_post(post_id, **fields)
