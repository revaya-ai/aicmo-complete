"""End-to-end orchestrator for the AI CMO pipeline.

Usage:
    python run.py "why your competitors all sound the same"

Creates one content post for the demo client and walks it through every station
in order, printing each status transition. The human gate and the ad spend gate
auto-approve so the full loop completes unattended. Runs GREEN against the stub
stations with the Python standard library only.
"""

import json
import sys

import db
from db import get_post

# Stations, in pipeline order. Each is a module exposing run(post_id, auto_approve).
from engine.brain import generate as brain_generate
from engine.studio import render as studio_render
from engine.studio import brand_qc as studio_brand_qc
from engine.mission import gate as mission_gate
from engine.mission import schedule as mission_schedule
from engine.mission import publish as mission_publish
from engine.mission import analytics as mission_analytics
from engine.ads import ads_agent

CLIENT = "lumen-skin"

# (label, station-module) in execution order.
PIPELINE = [
    ("brain.generate", brain_generate),
    ("studio.render", studio_render),
    ("studio.brand_qc", studio_brand_qc),
    ("mission.gate", mission_gate),
    ("mission.schedule", mission_schedule),
    ("mission.publish", mission_publish),
    ("mission.analytics", mission_analytics),
    ("ads.ads_agent", ads_agent),
]


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python run.py "<seed idea>"')
        sys.exit(1)
    seed_idea = sys.argv[1]

    db.init_db()
    post_id = db.create_post(CLIENT, seed_idea)
    print(f"Created post {post_id} for client '{CLIENT}'")
    print(f"Seed idea: {seed_idea}\n")

    for label, station in PIPELINE:
        before = get_post(post_id)["status"]
        station.run(post_id, auto_approve=True)
        after = get_post(post_id)["status"]
        if before == after:
            print(f"{before:<14} (no transition)  ({label})")
        else:
            print(f"{before:<14} -> {after:<16} ({label})")

    print("\nFinal row:")
    print(json.dumps(get_post(post_id), indent=2))


if __name__ == "__main__":
    main()
