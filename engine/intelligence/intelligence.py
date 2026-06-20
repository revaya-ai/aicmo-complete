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

2. REAL (opt in, behind env checks): DATAFORSEO_LOGIN, GSC_ACCESS_TOKEN plus
   GSC_SITE_URL, and APIFY_TOKEN turn on live keyword, search-console, and
   competitor scrapes. The real path shapes its output the same way the stub does
   so the Strategist keeps working unchanged. The real path is never taken
   without the matching env var, and the path label reports which sources ran.
"""

import os
import re

from engine.integrations.apify import ApifyClient
from engine.integrations.dataforseo import DataForSEOClient
from engine.integrations.gsc import GSCClient

# Default Apify actor used for competitor scrapes. A caller can override it by
# passing actor_id through to _apify_seeds. This is a real Apify Instagram scraper
# actor id; nothing runs unless APIFY_TOKEN is set and the live path is taken.
DEFAULT_APIFY_ACTOR = "apify/instagram-scraper"

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


def _gsc_seeds(pillars: list, gsc_client) -> list:
    """Build seeds from Google Search Console top queries, grounded in pillars.

    Pulls the recent top queries for the configured property and turns each into
    a reader-first seed line. Queries are mapped to pillars round-robin so the
    live demand still serves the strategy rather than landing all on one pillar.
    Every seed is labeled live:gsc so a reviewer can trace the source. Raises on
    any client error so the caller can fall back to the stub.
    """
    seeds = []
    if not pillars:
        return seeds
    resp = gsc_client.search_analytics(
        start_date="2024-01-01",
        end_date="2024-12-31",
        dimensions=["query"],
        row_limit=25,
    )
    for i, query in enumerate(_extract_gsc_queries(resp)):
        pillar = pillars[i % len(pillars)]
        seeds.append(
            {
                "idea": f"answer the search: {query}",
                "pillar": pillar,
                "source": "live:gsc",
                "signal": "real Search Console demand",
            }
        )
    return seeds


def _extract_gsc_queries(resp: dict) -> list:
    """Pull the query strings out of a Search Console searchAnalytics response.

    Tolerant of the rows -> keys shape. Returns [] if the response is empty or
    shaped differently, so a thin response degrades rather than crashing.
    """
    queries = []
    for row in (resp or {}).get("rows", []) or []:
        keys = (row or {}).get("keys") or []
        if keys and keys[0]:
            queries.append(keys[0])
    return queries


def _apify_seeds(pillars: list, apify_client, actor_id: str = DEFAULT_APIFY_ACTOR) -> list:
    """Build seeds from an Apify competitor scrape, grounded in client pillars.

    Runs a competitor-scrape actor and turns each returned item into a
    competitor-signal seed line. Items are mapped to pillars round-robin so the
    signal still serves the strategy. Every seed is labeled live:apify so a
    reviewer can trace the source. Raises on any client error so the caller can
    fall back to the stub.
    """
    seeds = []
    if not pillars:
        return seeds
    items = apify_client.run_actor_get_items(
        actor_id,
        {"resultsLimit": 25},
    )
    for i, hook in enumerate(_extract_apify_hooks(items)):
        pillar = pillars[i % len(pillars)]
        seeds.append(
            {
                "idea": f"react to a competitor angle: {hook}",
                "pillar": pillar,
                "source": "live:apify",
                "signal": "competitor signal from Apify",
            }
        )
    return seeds


def _extract_apify_hooks(items: list) -> list:
    """Pull short text hooks out of Apify dataset items.

    Tolerant of varied item shapes: tries caption, then text, then title. Returns
    [] if items are empty or shaped differently, so a thin response degrades
    rather than crashing.
    """
    hooks = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        text = item.get("caption") or item.get("text") or item.get("title")
        if text:
            hooks.append(str(text).strip().splitlines()[0][:120])
    return hooks


def sweep_with_meta(
    client: str = "lumen-skin",
    dfs_client=None,
    gsc_client=None,
    apify_client=None,
) -> dict:
    """Run the sweep and report which live sources ran. Returns {seeds, path}.

    The path label honestly composes from the live sources that contributed, in a
    fixed order: dataforseo, gsc, apify. So a DataForSEO-only run reports exactly
    "live:dataforseo"; all three report "live:dataforseo+gsc+apify"; nothing
    configured reports "offline:stub". On any client error that source is skipped
    and the sweep falls back, never crashing. No silent pretending: the path is
    always stated.

    The three client args let tests inject fakes. By default the real clients are
    constructed; with no credentials they are simply not configured and we stay
    offline.
    """
    pillars = load_pillars(client)
    if not pillars:
        return {"seeds": [], "path": "offline:stub"}

    if dfs_client is None:
        dfs_client = DataForSEOClient()
    if gsc_client is None:
        gsc_client = GSCClient()
    if apify_client is None:
        apify_client = ApifyClient()

    seeds = []
    sources = []

    if dfs_client.is_configured():
        try:
            live = _live_seeds(pillars, dfs_client)
            if live:
                seeds.extend(live)
                sources.append("dataforseo")
        except Exception:
            # Any client/network error falls back to the deterministic stub.
            pass

    if gsc_client.is_configured():
        try:
            live = _gsc_seeds(pillars, gsc_client)
            if live:
                seeds.extend(live)
                sources.append("gsc")
        except Exception:
            pass

    if apify_client.is_configured():
        try:
            live = _apify_seeds(pillars, apify_client)
            if live:
                seeds.extend(live)
                sources.append("apify")
        except Exception:
            pass

    if sources:
        return {"seeds": seeds, "path": "live:" + "+".join(sources)}

    return {"seeds": _stub_seeds(pillars), "path": "offline:stub"}


def sweep(
    client: str = "lumen-skin",
    dfs_client=None,
    gsc_client=None,
    apify_client=None,
) -> list:
    """Run the intelligence sweep. Returns a list of candidate seed-idea dicts.

    Each dict: {idea, pillar, source, signal}. Grounded in the client's strategy
    pillars. Deterministic and offline unless DataForSEO, GSC, or Apify
    credentials are present. Thin wrapper over sweep_with_meta for back-compat
    with the rest of the system.
    """
    return sweep_with_meta(
        client,
        dfs_client=dfs_client,
        gsc_client=gsc_client,
        apify_client=apify_client,
    )["seeds"]


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
