"""Off-site backup helper for pipeline artifacts.

backup_artifacts(paths) tries Backblaze first. When the Backblaze credentials
are present it uploads each file to the bucket. When they are not (the default),
it logs that it is using the offline no-op and records the artifacts to a local
manifest under outputs/backups/ instead. Stdlib only, no socket opened on the
offline path.

This is the same credential-gated pattern the integration clients use: the live
seam exists, but nothing leaves the machine until a key is set. The system stays
fully runnable offline with zero accounts.
"""

import json
import logging
import os
from datetime import datetime

from engine.integrations.backblaze import BackblazeClient, BackblazeNotConfigured

logger = logging.getLogger(__name__)

BACKUP_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "outputs", "backups"
)


def _now() -> str:
    return datetime.utcnow().isoformat()


def _write_manifest(entries: list, mode: str) -> str:
    """Write a manifest of backed-up artifacts to BACKUP_DIR. Returns its path."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    manifest_path = os.path.join(BACKUP_DIR, f"manifest-{stamp}.json")
    payload = {
        "created_at": _now(),
        "mode": mode,
        "artifacts": entries,
    }
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return manifest_path


def backup_artifacts(paths: list) -> dict:
    """Back up a list of local file paths.

    Returns {"mode": "backblaze"|"offline", "manifest": str, "artifacts": list}.
    Missing files are skipped. The offline path records a local manifest and
    opens no socket.
    """
    existing = [p for p in paths if os.path.exists(p)]
    client = BackblazeClient()

    if not client.is_configured():
        logger.info(
            "Backblaze not configured. Using offline no-op: recording %d "
            "artifact(s) to a local manifest under %s.",
            len(existing),
            BACKUP_DIR,
        )
        entries = [{"local_path": p, "remote_name": os.path.basename(p)} for p in existing]
        manifest_path = _write_manifest(entries, mode="offline")
        return {"mode": "offline", "manifest": manifest_path, "artifacts": entries}

    # Live path. Upload each file, then still write a manifest for the record.
    entries = []
    for path in existing:
        remote_name = os.path.basename(path)
        try:
            result = client.backup_file(path, remote_name)
        except BackblazeNotConfigured:
            # Defensive: credentials vanished between the check and the call.
            logger.warning("Backblaze became unconfigured mid-run; skipping %s", path)
            continue
        entries.append(
            {
                "local_path": path,
                "remote_name": remote_name,
                "file_id": result.get("fileId"),
            }
        )
    manifest_path = _write_manifest(entries, mode="backblaze")
    return {"mode": "backblaze", "manifest": manifest_path, "artifacts": entries}
