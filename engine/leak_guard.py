"""LEAK GUARD: the structural IP boundary from the deck.

The multi-repo model gives every client their own box. The rule that keeps the
model honest: a client box contains no other client's name. This module scans a
client-data folder and reports any foreign client name it finds, so a leak
surfaces before it ever reaches output.

Offline, stdlib only. It reads files and reports. It changes nothing.

scan_folder(path, known_clients) -> list of {file, match, line} leaks.
is_clean(path, known_clients)    -> True if no foreign names found.
"""

import os
import re

# File types worth scanning for a client name leak.
_TEXT_EXTS = {".md", ".txt", ".css", ".html", ".json", ".csv"}


def _own_name(folder: str) -> str:
    """The owning client's slug is the folder name (e.g. lumen-skin)."""
    return os.path.basename(os.path.normpath(folder)).lower()


def _name_variants(slug: str) -> list:
    """A client slug like 'darko-wines' can appear as the slug or as words.

    Returns lowercase regex-safe variants: the slug, and the spaced form.
    """
    spaced = slug.replace("-", " ")
    variants = {slug, spaced}
    return [re.escape(v) for v in variants if v]


def scan_folder(folder: str, known_clients: list) -> list:
    """Scan a client-data folder for any OTHER client's name.

    `known_clients` is the full roster of client slugs. The owning client (the
    folder name) is allowed; every other roster name found is a leak.
    Returns a list of {file, match, line} dicts, one per occurrence.
    """
    own = _own_name(folder)
    foreign = [c for c in known_clients if c.lower() != own]
    if not foreign:
        return []

    patterns = []
    for slug in foreign:
        for variant in _name_variants(slug.lower()):
            patterns.append((slug, re.compile(r"\b" + variant + r"\b", re.IGNORECASE)))

    leaks = []
    for root, _dirs, files in os.walk(folder):
        for fname in files:
            if os.path.splitext(fname)[1].lower() not in _TEXT_EXTS:
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, encoding="utf-8") as fh:
                    for lineno, line in enumerate(fh, start=1):
                        for slug, rx in patterns:
                            m = rx.search(line)
                            if m:
                                leaks.append(
                                    {
                                        "file": fpath,
                                        "client": slug,
                                        "match": m.group(0),
                                        "line": lineno,
                                    }
                                )
            except (UnicodeDecodeError, OSError):
                continue
    return leaks


def is_clean(folder: str, known_clients: list) -> bool:
    """True if the folder contains no foreign client name."""
    return not scan_folder(folder, known_clients)


def main():
    import argparse
    import json

    p = argparse.ArgumentParser(description="Scan a client-data folder for foreign client names.")
    p.add_argument("folder")
    p.add_argument("--clients", nargs="+", required=True, help="full roster of client slugs")
    a = p.parse_args()
    leaks = scan_folder(a.folder, a.clients)
    if leaks:
        print(json.dumps(leaks, indent=2))
        print(f"LEAK: {len(leaks)} foreign client name(s) found in {a.folder}")
        raise SystemExit(1)
    print(f"CLEAN: no foreign client names in {a.folder}")


if __name__ == "__main__":
    main()
