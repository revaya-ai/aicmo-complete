"""INTELLIGENCE LAYER — the front of the funnel.

Produces seed ideas from SEO/GEO/AEO signals, trends, and competitor signals.
Those seeds feed the Strategist (the Brain station) which turns one seed into one
on-brand draft.

Reads:  client-data/<client>/strategy.md  (the content pillars)
Writes: nothing to db.py. It emits candidate seed ideas as plain dicts. A human
        (or a future command) picks which seeds become posts via create_post +
        brain.generate. Intelligence never advances a row on its own.

Two paths:

1. DEFAULT (stdlib only, no keys, no network): build a deterministic list of
   candidate seed ideas grounded in the client's strategy pillars. Each seed is
   tagged with the pillar it serves and a stub source label so the demo runs
   fully offline.

2. REAL (opt in, behind env checks): DATAFORSEO_LOGIN / GSC_CREDENTIALS /
   APIFY_TOKEN turn on live keyword, search-console, and competitor scrapes. The
   real path shapes its output the same way the stub does so the Strategist keeps
   working unchanged. The real path is never taken without the matching env var.
"""

import os
import re

# Each pillar gets a small bank of grounded seed templates. The sweep fills the
# pillar name in and tags the source so a reviewer can see where it came from.
# These are deliberately generic skincare angles so the demo client lands real,
# usable ideas. The real path replaces these with live signals.
_SEED_BANK = {
    "Education": [
        "the one ingredient people overuse and what it does to skin",
        "why a 10 step routine works worse than a 3 step one",
        "the skincare claim that means nothing on a label",
    ],
    "Proof": [
        "a four week before and after with the exact products used",
        "what a refund taught us about a product that did not work",
        "an ingredient breakdown on our best selling serum",
    ],
    "Behind the studio": [
        "what a small batch making day actually looks like",
        "the two founders and the kitchen-table start of the brand",
        "a mistake we made early and what it cost us",
    ],
    "Offers": [
        "why the starter set is three products and not seven",
        "the guarantee explained, and why we can afford it",
    ],
}


def load_pillars(client: str) -> list:
    """Parse the named content pillars out of client-data/<client>/strategy.md.

    Pillars are written as a numbered list with a bold name, e.g.
    `1. **Education (40%)** ...`. We return the clean pillar names in file order
    (`Education`, `Proof`, `Behind the studio`, `Offers`). Returns [] if the file
    or the pillar block is missing.
    """
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "client-data", client, "strategy.md"
    )
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    pillars = []
    # Match a bold pillar name, stripping any trailing "(40%)" weight.
    for m in re.finditer(r"^\s*\d+\.\s*\*\*(.+?)\*\*", text, flags=re.MULTILINE):
        name = re.sub(r"\s*\(.*?\)\s*$", "", m.group(1)).strip()
        if name and name not in pillars:
            pillars.append(name)
    return pillars


def _stub_seeds(pillars: list) -> list:
    """Deterministic candidate seeds grounded in the client's real pillars."""
    seeds = []
    for pillar in pillars:
        for idea in _SEED_BANK.get(pillar, []):
            seeds.append(
                {
                    "idea": idea,
                    "pillar": pillar,
                    "source": "stub:strategy-pillars",
                    "signal": "grounded in client strategy.md (no live data)",
                }
            )
    return seeds


def sweep(client: str = "lumen-skin") -> list:
    """Run the intelligence sweep. Returns a list of candidate seed-idea dicts.

    Each dict: {idea, pillar, source, signal}. Grounded in the client's strategy
    pillars. Deterministic and offline unless a real-data env var is set.
    """
    pillars = load_pillars(client)
    if not pillars:
        return []

    use_real = any(
        os.environ.get(v)
        for v in ("DATAFORSEO_LOGIN", "GSC_CREDENTIALS", "APIFY_TOKEN")
    )
    if use_real:
        # Real path would query DataForSEO (keyword/SERP), Google Search Console
        # (real queries already ranking), and Apify (competitor posts), then map
        # each signal onto a strategy pillar. It must return the same dict shape
        # as the stub. Left as the upgrade seam; we never reach it offline.
        return _stub_seeds(pillars)

    return _stub_seeds(pillars)


def main():
    import argparse
    import json

    p = argparse.ArgumentParser(description="Run the intelligence sweep for a client.")
    p.add_argument("--client", default="lumen-skin")
    a = p.parse_args()
    print(json.dumps(sweep(a.client), indent=2))


if __name__ == "__main__":
    main()
