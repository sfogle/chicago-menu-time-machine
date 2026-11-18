#!/usr/bin/env python3
"""Refresh venue facts in menus.json from venues.py without re-running the importers.

The importers copy what venues.py knows (pin, years, what stands there today,
the sourced history in venue_history.py) into each menu entry when they build
it. After editing venues.py or venue_history.py, run this to push the changes
into the menus already in menus.json:

    python apply_venue_history.py            # update in place
    python apply_venue_history.py --dry-run  # report what would change

Menu names and dishes are never touched. Cuisine, emoji and blurb are only
filled in where the entry still has the importer's placeholder.

Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from venues import KNOWN_VENUES, RAILROADS, standing, venue_key

DEFAULT_MENUS = Path(__file__).resolve().parent.parent / "frontend" / "public" / "data" / "menus.json"
PLACEHOLDER_BLURB = re.compile(r"^((breakfast|lunch|luncheon|dinner|supper|wine|drinks?|dessert)\s+)?(menu|card)\s+(for|from)\b",
                               re.IGNORECASE)
RAILROAD_BY_NAME = {entry["name"]: entry for entry in RAILROADS.values()}


def known_for(entry: dict) -> tuple[str | None, dict, bool]:
    """(venue key, known facts, is_railroad) for a menu entry."""
    if entry["name"] in RAILROAD_BY_NAME:
        return None, RAILROAD_BY_NAME[entry["name"]], True
    key = venue_key(entry["name"])
    return key, KNOWN_VENUES.get(key or "", {}), False


def refresh(entry: dict) -> list[str]:
    key, known, railroad = known_for(entry)
    if not known:
        return []
    before = json.dumps(entry, sort_keys=True, ensure_ascii=False)
    changed: list[str] = []

    entry["stillStanding"] = standing(known)
    if "lat" in known:
        entry["address"], entry["lat"], entry["lng"] = known["address"], known["lat"], known["lng"]
        entry["location"] = {"method": "hand-entered"}
    if not railroad:
        year = entry["year"]
        entry["opened"] = known.get("opened", year)
        entry["closed"] = known.get("closed", None if "opened" in known else year)
        entry["yearsKnown"] = "opened" in known
        if entry.get("venue") != key and entry.get("source") == "cia":
            entry["venue"] = key
        if entry.get("cuisine") in (None, "", "Restaurant") and known.get("cuisine"):
            entry["cuisine"] = known["cuisine"]
        if entry.get("emoji") in (None, "", "🍽️") and known.get("emoji"):
            entry["emoji"] = known["emoji"]
        if (not entry.get("blurb") or PLACEHOLDER_BLURB.match(entry["blurb"])) and known.get("blurb"):
            entry["blurb"] = known["blurb"]

    if json.dumps(entry, sort_keys=True, ensure_ascii=False) != before:
        changed.append(f"{entry['name']} ({entry['year']})")
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--menus", type=Path, default=DEFAULT_MENUS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    data = json.loads(args.menus.read_text())
    changed = [line for entry in data["restaurants"] for line in refresh(entry)]
    with_history = sum(1 for r in data["restaurants"] if r["stillStanding"].get("history"))
    print(f"{len(changed)} of {len(data['restaurants'])} menus updated; {with_history} now carry a sourced history.")
    for line in changed:
        print("  " + line)
    if not args.dry_run:
        args.menus.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
