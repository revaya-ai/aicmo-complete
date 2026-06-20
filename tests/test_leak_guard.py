"""Tests for the leak guard (structural IP boundary).

A client box must never contain another client's name. scan_folder returns the
list of foreign client names found in a client-data folder. Offline, stdlib only.
"""
import os

from engine import leak_guard


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def test_clean_folder_has_no_leaks(tmp_path):
    client_dir = tmp_path / "lumen-skin"
    _write(str(client_dir / "strategy.md"), "Lumen Skin Studio sells skincare.")
    leaks = leak_guard.scan_folder(str(client_dir), known_clients=["lumen-skin", "darko-wines"])
    assert leaks == []


def test_foreign_name_is_detected(tmp_path):
    client_dir = tmp_path / "lumen-skin"
    _write(
        str(client_dir / "notes.md"),
        "We did this for Darko Wines last quarter, reuse it here.",
    )
    leaks = leak_guard.scan_folder(
        str(client_dir), known_clients=["lumen-skin", "darko-wines"]
    )
    assert any("darko" in leak["match"].lower() for leak in leaks)
    assert leaks[0]["file"].endswith("notes.md")


def test_own_name_is_not_a_leak(tmp_path):
    client_dir = tmp_path / "darko-wines"
    _write(str(client_dir / "strategy.md"), "Darko Wines is the client.")
    leaks = leak_guard.scan_folder(
        str(client_dir), known_clients=["lumen-skin", "darko-wines"]
    )
    assert leaks == []


def test_check_returns_true_when_clean(tmp_path):
    client_dir = tmp_path / "lumen-skin"
    _write(str(client_dir / "strategy.md"), "All about lumen-skin.")
    assert leak_guard.is_clean(str(client_dir), known_clients=["lumen-skin", "darko-wines"]) is True
