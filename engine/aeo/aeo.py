"""AEO visibility: is the client cited when AI answers its target questions.

Two entry points:

    ai_visibility_report(client_slug, dfs_client=None) -> dict
        Build the visibility picture as a plain dict. Offline by default,
        deterministic. Live only when a configured DataForSEO client is present.

    write_ai_visibility_report(client_slug, dfs_client=None) -> str
        Render the dict to a markdown report at
        outputs/reports/<client>-aeo-visibility.md. Returns the path.

The report reads the client's target questions and keywords from
client-data/<client>/positioning.md and strategy.md. When DataForSEO is
configured it pulls AI search volume (ai_keyword_data) and brand mentions
(llm_mentions). When not configured it produces a deterministic offline mock so
the report runs for anyone. The data source is always stated in the report.

No em dashes in generated markdown. No network in the offline path.
"""

import os
import re

from engine.integrations.dataforseo import DataForSEOClient

_CLIENT_DATA = os.path.join(os.path.dirname(__file__), "..", "..", "client-data")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "outputs", "reports")


def _read(client_slug: str, filename: str) -> str:
    path = os.path.join(_CLIENT_DATA, client_slug, filename)
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _brand_name(client_slug: str) -> str:
    """Best-effort brand name from positioning.md, else a titled slug."""
    positioning = _read(client_slug, "positioning.md")
    m = re.search(r"^#\s*Positioning:\s*(.+)$", positioning, flags=re.MULTILINE)
    if m:
        return m.group(1).strip()
    return client_slug.replace("-", " ").title()


def load_target_queries(client_slug: str) -> list:
    """Derive the target questions and keywords for the client.

    Pulls noun-phrase signals from positioning.md (the problem and promise) and
    the pillar names from strategy.md, then frames each as a question a buyer
    might ask an AI. Deterministic so the offline report is stable. Returns a
    de-duplicated list of query strings.
    """
    brand = _brand_name(client_slug)
    positioning = _read(client_slug, "positioning.md")
    strategy = _read(client_slug, "strategy.md")

    queries = []

    # Pillar names become topic questions.
    for m in re.finditer(r"^\s*\d+\.\s*\*\*(.+?)\*\*", strategy, flags=re.MULTILINE):
        name = re.sub(r"\s*\(.*?\)\s*$", "", m.group(1)).strip().lower()
        if name:
            queries.append(f"best {name} advice for {brand} customers")

    # The one-line promise becomes a direct buyer question.
    one_line = re.search(r"\*\*One-line:\*\*\s*(.+)", positioning)
    if one_line:
        queries.append(one_line.group(1).strip().rstrip("."))

    # A standing brand-citation query.
    queries.append(f"is {brand} a good choice")

    # De-duplicate, preserve order.
    seen = set()
    deduped = []
    for q in queries:
        key = q.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(q)
    return deduped


def _offline_visibility(queries: list) -> list:
    """Deterministic offline mock of per-query AI visibility."""
    rows = []
    for i, q in enumerate(queries):
        rows.append(
            {
                "query": q,
                "ai_search_volume": None,
                "brand_mentioned": False,
                "sentiment": "unknown",
                "note": "offline mock, no live AI data",
            }
        )
    return rows


def _live_visibility(client_slug: str, queries: list, dfs_client) -> list:
    """Pull AI search volume and brand mentions for each query."""
    brand = _brand_name(client_slug)
    rows = []
    volume = {}
    try:
        resp = dfs_client.ai_keyword_data(queries)
        for task in resp.get("tasks", []):
            for result in task.get("result", []) or []:
                for item in result.get("items", []) or []:
                    kw = item.get("keyword")
                    if kw:
                        volume[kw] = item.get("ai_search_volume")
    except Exception:
        volume = {}

    for q in queries:
        mentioned = False
        sentiment = "unknown"
        try:
            mresp = dfs_client.llm_mentions(f"{q} {brand}")
            for task in mresp.get("tasks", []):
                for result in task.get("result", []) or []:
                    for item in result.get("items", []) or []:
                        mentioned = bool(item.get("mentioned", mentioned))
                        sentiment = item.get("sentiment", sentiment)
        except Exception:
            pass
        rows.append(
            {
                "query": q,
                "ai_search_volume": volume.get(q),
                "brand_mentioned": mentioned,
                "sentiment": sentiment,
                "note": "live DataForSEO AI data",
            }
        )
    return rows


def ai_visibility_report(client_slug: str, dfs_client=None) -> dict:
    """Build the AI visibility report as a dict. Offline by default."""
    if dfs_client is None:
        dfs_client = DataForSEOClient()

    queries = load_target_queries(client_slug)
    brand = _brand_name(client_slug)

    if dfs_client.is_configured():
        rows = _live_visibility(client_slug, queries, dfs_client)
        path = "live:dataforseo"
    else:
        rows = _offline_visibility(queries)
        path = "offline:stub"

    cited = sum(1 for r in rows if r["brand_mentioned"])
    return {
        "client": client_slug,
        "brand": brand,
        "path": path,
        "queries": queries,
        "rows": rows,
        "summary": {
            "total_queries": len(queries),
            "cited": cited,
            "uncited": len(queries) - cited,
        },
    }


def _render_markdown(report: dict) -> str:
    """Render the report dict to markdown. No em dashes."""
    source = (
        "Live DataForSEO AI optimization data"
        if report["path"] == "live:dataforseo"
        else "Offline deterministic mock (no live data, set DataForSEO credentials to go live)"
    )
    lines = []
    lines.append(f"# AEO Visibility Report: {report['brand']}")
    lines.append("")
    lines.append(f"Client: {report['client']}")
    lines.append(f"Data source: {source}")
    lines.append(f"Path: {report['path']}")
    lines.append("")
    s = report["summary"]
    lines.append("## Summary")
    lines.append("")
    lines.append(f"Target queries checked: {s['total_queries']}")
    lines.append(f"Queries where the brand is cited: {s['cited']}")
    lines.append(f"Queries with no brand citation: {s['uncited']}")
    lines.append("")
    lines.append("## Query detail")
    lines.append("")
    lines.append("| Query | AI search volume | Brand cited | Sentiment | Note |")
    lines.append("| --- | --- | --- | --- | --- |")
    for r in report["rows"]:
        vol = r["ai_search_volume"] if r["ai_search_volume"] is not None else "n/a"
        cited = "yes" if r["brand_mentioned"] else "no"
        lines.append(
            f"| {r['query']} | {vol} | {cited} | {r['sentiment']} | {r['note']} |"
        )
    lines.append("")
    lines.append("## What to do with this")
    lines.append("")
    lines.append(
        "Every uncited query is a content gap. Write a post that answers the "
        "question plainly so an AI answer has something to cite. Re-run this "
        "report after publishing to track movement."
    )
    lines.append("")
    return "\n".join(lines)


def write_ai_visibility_report(client_slug: str, dfs_client=None) -> str:
    """Build and write the markdown report. Returns the file path."""
    report = ai_visibility_report(client_slug, dfs_client=dfs_client)
    markdown = _render_markdown(report)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, f"{client_slug}-aeo-visibility.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(markdown)
    return path


def main():
    import argparse

    p = argparse.ArgumentParser(description="Run the AEO visibility report.")
    p.add_argument("--client", default="lumen-skin")
    a = p.parse_args()
    path = write_ai_visibility_report(a.client)
    report = ai_visibility_report(a.client)
    print(f"[aeo] path: {report['path']}")
    print(f"[aeo] wrote report to {path}")


if __name__ == "__main__":
    main()
