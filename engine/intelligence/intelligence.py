"""INTELLIGENCE LAYER: the front of the funnel.

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

from engine.integrations.dataforseo import DataForSEOClient

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


# A small per-pillar bank of seed keywords used to query DataForSEO when it is
# configured. The keywords stay grounded in the client's pillars so the live
# results still serve the strategy, not a random keyword dump.
_PILLAR_KEYWORD_SEEDS = {
    "Education": ["simple skincare routine", "skincare ingredients to skip"],
    "Proof": ["skincare before and after", "best selling serum ingredients"],
    "Behind the studio": ["small batch skincare", "indie skincare brand"],
    "Offers": ["skincare starter set", "skincare money back guarantee"],
}


def _live_seeds(pillars: list, dfs_client) -> list:
    """Build seeds from DataForSEO keyword ideas, grounded in client pillars.

    For each pillar we ask the client for keyword ideas around that pillar's
    seed keywords, then turn the returned keyword strings into reader-first seed
    lines. Every seed is tagged to a real pillar and labeled live:dataforseo so a
    reviewer can trace the source. Raises on any client error so the caller can
    fall back to the stub.
    """
    seeds = []
    for pillar in pillars:
        keywords = _PILLAR_KEYWORD_SEEDS.get(pillar)
        if not keywords:
            continue
        resp = dfs_client.keyword_ideas(keywords)
        for kw in _extract_keywords(resp):
            seeds.append(
                {
                    "idea": f"answer the search: {kw}",
                    "pillar": pillar,
                    "source": "live:dataforseo",
                    "signal": "real keyword demand from DataForSEO Labs",
                }
            )
    return seeds


def _extract_keywords(resp: dict) -> list:
    """Pull the keyword strings out of a DataForSEO keyword_ideas response.

    Tolerant of the nested tasks -> result -> items shape. Returns [] if the
    response is empty or shaped differently, so a thin response degrades to the
    stub rather than crashing.
    """
    keywords = []
    for task in (resp or {}).get("tasks", []):
        for result in (task or {}).get("result", []) or []:
            for item in (result or {}).get("items", []) or []:
                kw = item.get("keyword")
                if kw:
                    keywords.append(kw)
    return keywords


def sweep_with_meta(client: str = "lumen-skin", dfs_client=None) -> dict:
    """Run the sweep and report which path ran. Returns {seeds, path}.

    path is "live:dataforseo" when the injected (or default) DataForSEO client is
    configured and returns usable keywords, otherwise "offline:stub". On any
    client error the sweep falls back to the offline stub. No silent pretending:
    the path is always stated.

    dfs_client lets tests inject a fake. By default the real client is
    constructed; with no credentials it is simply not configured and we stay
    offline.
    """
    pillars = load_pillars(client)
    if not pillars:
        return {"seeds": [], "path": "offline:stub"}

    if dfs_client is None:
        dfs_client = DataForSEOClient()

    if dfs_client.is_configured():
        try:
            live = _live_seeds(pillars, dfs_client)
            if live:
                return {"seeds": live, "path": "live:dataforseo"}
        except Exception:
            # Any client/network error falls back to the deterministic stub.
            pass

    return {"seeds": _stub_seeds(pillars), "path": "offline:stub"}


def sweep(client: str = "lumen-skin", dfs_client=None) -> list:
    """Run the intelligence sweep. Returns a list of candidate seed-idea dicts.

    Each dict: {idea, pillar, source, signal}. Grounded in the client's strategy
    pillars. Deterministic and offline unless DataForSEO credentials are present.
    Thin wrapper over sweep_with_meta for back-compat with the rest of the system.
    """
    return sweep_with_meta(client, dfs_client=dfs_client)["seeds"]


def main():
    import argparse
    import json

    p = argparse.ArgumentParser(description="Run the intelligence sweep for a client.")
    p.add_argument("--client", default="lumen-skin")
    a = p.parse_args()
    result = sweep_with_meta(a.client)
    print(f"[intelligence] path: {result['path']}")
    print(json.dumps(result["seeds"], indent=2))


if __name__ == "__main__":
    main()
