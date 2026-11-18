#!/usr/bin/env python3
"""Add NYPL menus that volunteers never transcribed, by OCR of their scans.

Nearly every Chicago menu NYPL has scanned is already in the transcribed
"What's on the Menu?" dataset (import_nypl_chicago.py). A check against the
Digital Collections API in November 2026 found 1,207 Chicago menu page scans,
of which only 16 were missing from the dataset, from three menus. One of those
is worth having: Gunther's 1900 "Complete Menu", four priced pages against the
transcribed Gunther's menu's one. That is what MENUS lists.

For each menu it downloads the listed page scans from NYPL's public IIIF image
server into pipeline/raw_scans/ (gitignored), OCRs them, and writes one
multi-page entry to menus.json. The entry replaces any other entry for the
same venue and year. The app loads the pages from iiif.nypl.org, as it does for
the transcribed NYPL menus; no image is stored in the repo and no API token is
needed. Then run clean_menus.py --only ocr.

    .venv/bin/python import_nypl_scans.py --dry-run
    .venv/bin/python import_nypl_scans.py

To find candidates again, pipeline/nypl_api.py talks to the API (token needed).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request

import fetch_and_ocr_chicago as fetch
import ocr_menu
from venues import KNOWN_VENUES, standing

IIIF = "https://iiif.nypl.org/iiif/3/{id}/full/{w},/0/default.jpg"
FALLBACK = "https://images.nypl.org/index.php?id={id}&t=w"
ITEM = "https://digitalcollections.nypl.org/items/{uuid}"
OCR_WIDTH = 1400  # px; dish boxes are stored in this image's coordinates
SHOW_WIDTH = 1000  # px; what the app loads, like the transcribed NYPL menus

MENUS = [
    {
        "id": "nyplscan-gunthers-1900",
        "venue": "gunther",
        "year": 1900,
        "title": "COMPLETE MENU [held by] GUNTHER'S [at] \"CHICAGO, IL.\"",
        # (image id, capture uuid) in menu order: oysters, lobster and fish, grill, drinks.
        # The other captures of this item are blank backs or second scans of these pages.
        "pages": [
            ("4000009431", "510d47db-4aa3-a3d9-e040-e00a18064a99"),
            ("4000009430", "510d47db-4aa2-a3d9-e040-e00a18064a99"),
            ("4000009437", "510d47db-4aa9-a3d9-e040-e00a18064a99"),
            ("4000009433", "510d47db-4aa5-a3d9-e040-e00a18064a99"),
        ],
    },
]

TRAILING_PRICES = re.compile(r"(\s+\d{1,3}(\.\d\d)?)+$")  # "Blue Points 50" (a second price column)


def download(image_id: str) -> fetch.Path:
    dest = fetch.RAW_DIR / f"nyplapi-{image_id}.jpg"
    if not dest.exists():
        time.sleep(fetch.PAUSE)
        req = urllib.request.Request(IIIF.format(id=image_id, w=OCR_WIDTH), headers={"User-Agent": fetch.USER_AGENT})
        with urllib.request.urlopen(req, timeout=60) as resp:
            blob = resp.read()
        if not blob.startswith(b"\xff\xd8"):
            raise SystemExit(f"{image_id}: not a JPEG")
        dest.write_bytes(blob)
    return dest


def build(spec: dict, engine: str) -> dict:
    known = KNOWN_VENUES[spec["venue"]]
    year = spec["year"]
    pages, dishes, engines = [], [], set()
    for index, (image_id, uuid) in enumerate(spec["pages"]):
        web = fetch.web_copy(download(image_id))
        fragments, used = fetch.ocr_cached(web, engine)
        engines.add(used)
        found = fetch.plausible(ocr_menu.parse_menu(ocr_menu.cluster_rows(fragments), year), year, known["name"])
        with fetch.Image.open(web) as im:
            width, height = im.size
        pages.append({
            "src": IIIF.format(id=image_id, w=SHOW_WIDTH),
            "fallbackSrc": FALLBACK.format(id=image_id),
            "width": width, "height": height,
            "sourceUrl": ITEM.format(uuid=uuid),
        })
        for d in found:
            d["name"] = TRAILING_PRICES.sub("", d["name"]).strip()
            d["page"] = index
            dishes.append(d)
        print(f"  page {index + 1} ({image_id}): {len(found)} priced dishes ({used})", file=sys.stderr)

    seen, menu = set(), []
    for d in dishes:
        slug = d.pop("_slug")
        dish_id = f"{spec['id']}-{slug}"
        if dish_id in seen:
            continue
        seen.add(dish_id)
        menu.append({"id": dish_id, **d})
    confidences = [d["confidence"] for d in menu]
    return {
        "id": spec["id"],
        "venue": spec["venue"],
        "name": known["name"],
        "year": year,
        "opened": known.get("opened", year),
        "closed": known.get("closed", None if "opened" in known else year),
        "yearsKnown": "opened" in known,
        "address": known["address"], "lat": known["lat"], "lng": known["lng"],
        "cuisine": known["cuisine"], "emoji": known["emoji"], "blurb": known["blurb"],
        "stillStanding": standing(known),
        "scan": {
            **pages[0],
            "placeholder": False,
            "credit": "New York Public Library, Rare Book Division (Buttolph Collection of Menus). "
                      "Not transcribed by volunteers; dishes read by OCR.",
            "license": "No Copyright - United States (NoC-US 1.0)",
        },
        "pages": pages,
        "source": "nypl-scan",
        "location": {"method": "hand-entered"},
        "ocr": {
            "engine": "/".join(sorted(engines)),
            "meanConfidence": round(sum(confidences) / len(confidences), 1) if confidences else None,
            "processed": time.strftime("%Y-%m-%d"),
        },
        "menu": menu,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", choices=["auto", "paddle", "tesseract"], default="paddle")
    p.add_argument("--menus", type=fetch.Path, default=ocr_menu.DEFAULT_MENUS)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    for d in (fetch.RAW_DIR, fetch.WEB_DIR, fetch.CACHE_DIR):
        d.mkdir(parents=True, exist_ok=True)

    doc = json.loads(args.menus.read_text())
    for spec in MENUS:
        print(f"{spec['title']} ({spec['year']})", file=sys.stderr)
        entry = build(spec, args.engine)
        replaced = [r for r in doc["restaurants"]
                    if r["id"] == entry["id"] or (r.get("venue"), r["year"]) == (entry["venue"], entry["year"])]
        for r in replaced:
            print(f"  replaces {r['id']} ({len(r['menu'])} dishes)", file=sys.stderr)
        print(f"  -> {entry['id']}: {len(entry['menu'])} dishes on {len(entry['pages'])} pages", file=sys.stderr)
        doc["restaurants"] = [r for r in doc["restaurants"] if r not in replaced] + [entry]
    doc["restaurants"].sort(key=lambda r: (r["year"], r["name"]))
    if args.dry_run:
        print("--dry-run: menus.json not written", file=sys.stderr)
        return 0
    args.menus.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"wrote {args.menus}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
