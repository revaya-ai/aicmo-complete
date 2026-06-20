"""Tests for Station 1: Brain generate (deterministic offline stand-in).

Verifies the draft is grounded in the real client context: the pillar comes from
strategy.md (not a hardcoded constant), and the body references real context
(the primary audience parsed from brand-and-audience.md), not a fixed string.
"""
import db as db_module
from engine.brain.generate import (
    parse_pillars,
    parse_primary_audience,
    pick_pillar,
)


def _fresh_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "t.db"))
    db_module.init_db()


def _captured_post(seed):
    return db_module.create_post(client="lumen-skin", seed_idea=seed)


def test_parse_pillars_reads_strategy_file():
    strategy = (
        "# Strategy\n\n## Content pillars\n"
        "1. **Education (40%)** teach.\n"
        "2. **Proof (25%)** before/afters.\n"
        "3. **Behind the studio (20%)** founders.\n"
        "4. **Offers (15%)** the set.\n\n## Cadence\n4 posts.\n"
    )
    pillars = parse_pillars(strategy)
    assert pillars == ["Education", "Proof", "Behind the studio", "Offers"]


def test_parse_primary_audience():
    brand = (
        "# Brand\n\n## Primary audience\n"
        '**"Overwhelmed Olivia"** 32, works full time.\n'
    )
    assert parse_primary_audience(brand) == "Overwhelmed Olivia"


def test_pick_pillar_is_deterministic_and_from_list():
    pillars = ["Education", "Proof", "Behind the studio", "Offers"]
    a = pick_pillar(pillars, "seed-one")
    b = pick_pillar(pillars, "seed-one")
    assert a == b
    assert a in pillars


def test_run_pillar_comes_from_strategy_not_constant(monkeypatch, tmp_path):
    """The chosen pillar must be one of the REAL strategy pillars, and across a
    range of seeds we must see more than just 'Education' (proving it is not a
    hardcoded constant)."""
    _fresh_db(monkeypatch, tmp_path)
    from engine.brain import generate

    # The real strategy pillars for lumen-skin.
    real_pillars = parse_pillars(generate._read("lumen-skin", "strategy.md"))
    assert real_pillars, "strategy.md yielded no pillars"

    chosen = set()
    for seed in [f"idea number {i} about skincare honesty" for i in range(20)]:
        pid = _captured_post(seed)
        generate.run(pid)
        row = db_module.get_post(pid)
        assert row["pillar"] in real_pillars
        chosen.add(row["pillar"])

    # Across 20 seeds we should hit more than one pillar; a constant would not.
    assert len(chosen) > 1, f"pillar looks hardcoded, only saw {chosen}"


def test_run_body_references_real_context(monkeypatch, tmp_path):
    """The body must reference the real audience parsed from the client context,
    not a fixed canned string."""
    _fresh_db(monkeypatch, tmp_path)
    from engine.brain import generate

    audience = parse_primary_audience(
        generate._read("lumen-skin", "brand-and-audience.md")
    )
    assert audience, "no primary audience parsed"

    pid = _captured_post("why competitors all sound the same")
    generate.run(pid)
    row = db_module.get_post(pid)
    assert row["status"] == "drafted"
    assert audience in row["body"], "body does not reference the real audience"
    assert "why competitors all sound the same" in row["body"]
