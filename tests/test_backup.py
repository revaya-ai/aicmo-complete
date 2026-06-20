"""Tests for the backup helper (engine/mission/backup.py).

The helper tries Backblaze first and, when unconfigured, falls back to an
offline no-op that records the artifacts to a local manifest under
outputs/backups/. The offline path is stdlib only and opens no socket.

These tests run with Backblaze credentials unset, so backup_artifacts must use
the offline manifest path. We point the manifest dir at tmp_path and assert a
manifest is written listing the artifacts, with no network call.
"""

import json

import pytest

from engine.mission import backup


def test_offline_path_writes_manifest_no_network(monkeypatch, tmp_path):
    monkeypatch.delenv("BACKBLAZE_KEY_ID", raising=False)
    monkeypatch.delenv("BACKBLAZE_APPLICATION_KEY", raising=False)
    monkeypatch.delenv("BACKBLAZE_BUCKET", raising=False)

    # Guard: any network attempt fails the test loudly.
    from engine.integrations import backblaze

    monkeypatch.setattr(
        backblaze.urllib.request,
        "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network was called")),
    )

    backups_dir = tmp_path / "backups"
    monkeypatch.setattr(backup, "BACKUP_DIR", str(backups_dir))

    a = tmp_path / "a.txt"
    a.write_text("alpha")
    b = tmp_path / "b.txt"
    b.write_text("beta")

    result = backup.backup_artifacts([str(a), str(b)])

    assert result["mode"] == "offline"
    manifest_path = result["manifest"]
    data = json.loads(open(manifest_path, encoding="utf-8").read())
    names = [entry["local_path"] for entry in data["artifacts"]]
    assert str(a) in names
    assert str(b) in names
    assert data["mode"] == "offline"


def test_offline_skips_missing_files(monkeypatch, tmp_path):
    monkeypatch.delenv("BACKBLAZE_KEY_ID", raising=False)
    monkeypatch.delenv("BACKBLAZE_APPLICATION_KEY", raising=False)
    monkeypatch.delenv("BACKBLAZE_BUCKET", raising=False)
    monkeypatch.setattr(backup, "BACKUP_DIR", str(tmp_path / "backups"))

    real = tmp_path / "real.txt"
    real.write_text("here")

    result = backup.backup_artifacts([str(real), str(tmp_path / "missing.txt")])
    data = json.loads(open(result["manifest"], encoding="utf-8").read())
    names = [entry["local_path"] for entry in data["artifacts"]]
    assert str(real) in names
    assert str(tmp_path / "missing.txt") not in names
