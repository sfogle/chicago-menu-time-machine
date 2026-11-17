#!/usr/bin/env python3
"""Import Chicago menus from the Culinary Institute of America menu collection.

The CIA's Conrad N. Hilton Library publishes its menu collection on CONTENTdm
(https://cdm16940.contentdm.oclc.org/digital/collection/p16940coll1). Each
record has a city, a decade, usually a street address, and a typed transcript
of every page, so dishes and prices come from the transcript, not from OCR.
It fills the decades NYPL's dataset has nothing for (1930s, 1980s).

    python3 import_cia_chicago.py --dry-run                 # show what would be imported
    python3 import_cia_chicago.py                           # 1930s + 1980s into menus.json
    python3 import_cia_chicago.py --decades 1940s 1950s     # other decades
    python3 import_cia_chicago.py --no-locate               # skip the highlight boxes

The transcript says what is on a page but not where. If the `tesseract`
program is installed, each page image is OCR'd once, only to find where each
transcribed dish sits, and the dish gets a `bbox`. Without it (or with
--no-locate) dishes are imported without a highlight box.

Replaces every `cia-*` entry for the chosen decades in menus.json and leaves
the rest alone. Standard library only. Being polite to the CIA's server: one
request a second, every answer cached in the gitignored pipeline/cia_data/,
and page images requested at most 1600px on the long side, never full size.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import io
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from clean_menus import categorize, clean_name, looks_like_dish, sort_menu, title_case
from import_nypl_chicago import USER_AGENT, locate, price_ceiling
from venues import KNOWN_VENUES, venue_key

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "cia_data"
DEFAULT_MENUS = HERE.parent / "frontend" / "public" / "data" / "menus.json"

HOST = "https://cdm16940.contentdm.oclc.org"
COLLECTION = "p16940coll1"
QUERY_URL = (HOST + "/digital/bl/dmwebservices/index.php?q=dmQuery/" + COLLECTION
             + "/locati%5EChicago%5Eall%5Eand!decade%5E{decade}%5Eall%5Eand/title!date/date/200/1/1/0/0/0/0/0/json")
ITEM_API = HOST + "/digital/api/collections/" + COLLECTION + "/items/{id}/false"
ITEM_URL = HOST + "/digital/collection/" + COLLECTION + "/id/{id}"
IMAGE_MAX = 1600  # px on the long side. Double-page spreads are unreadable below this.
IMAGE_URL = HOST + "/iiif/2/" + COLLECTION + ":{id}/full/!{max},{max}/0/default.jpg"
PAUSE = 1.0  # seconds between requests to the CIA's server

EVENT_SKIP = re.compile(r"banquet|annual|anniversary|convention|reunion|reception|in honor", re.IGNORECASE)
# a price at the end of a cell: 1.65  $1.65  .45  35c  65  105
PRICE = r"\$?\s?(?:\d{1,2}\.\d{2}|\.\d{2}|\d{2,3})\s?[c¢]?"
PRICE_END = re.compile(rf"(?:(?<=\s)|(?<=,)|(?<=[A-Za-z)])(?=\$?\s?\.\d)|^)({PRICE})(?:\s?-\s?{PRICE}|\.?\s+{PRICE})?\.?\s*$")
PRICE_INLINE = re.compile(rf"(?<=\s)({PRICE})(?:\s?-\s?{PRICE})?(?=\s|$)")
NOT_A_DISH = re.compile(r"\b(extra|additional|minimum|phone|call|telephone|served from|a\.m\.|p\.m\.|calories|"
                        r"copyright|chicago, il|served for)", re.IGNORECASE)
SIZE_WORD = re.compile(r"^(small|large|half|double|glass|bottle|each|cold|per person)$", re.IGNORECASE)


def get_json(url: str, cache_name: str):
    """GET a JSON document, once: answers are cached on disk."""
    cache = DATA_DIR / cache_name
    if cache.exists():
        return json.loads(cache.read_text())
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read())
    cache.write_text(json.dumps(data))
    time.sleep(PAUSE)
    return data


def get_image(page_id: int) -> Path:
    cache = DATA_DIR / f"page_{page_id}.jpg"
    if not cache.exists():
        request = urllib.request.Request(IMAGE_URL.format(id=page_id, max=IMAGE_MAX), headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=60) as response:
            cache.write_bytes(response.read())
        time.sleep(PAUSE)
    return cache


# ---------------------------------------------------------------------------
# Transcript -> dishes
# ---------------------------------------------------------------------------
def to_price(token: str, year: int) -> float | None:
    token = token.strip().lower().replace(" ", "")
    cents = token.endswith(("c", "¢"))
    token = token.strip("$c¢")
    try:
        value = float(token)
    except ValueError:
        return None
    if "." not in token:  # "65" and "105" are cents; so is "40c"
        value /= 100
    elif cents:
        value /= 100
    return round(value, 2) if 0 < value <= price_ceiling(year) else None


def split_cells(line: str) -> list[tuple[str, str | None]]:
    """Split one transcript line into (text, price) cells; price is None if the line has none."""
    end = PRICE_END.search(line)
    if not end:
        return [(line, None)]
    cells, start = [], 0
    for m in PRICE_INLINE.finditer(line[:end.start()]):
        text = line[start:m.start()]
        if re.search(r"[A-Za-z]{3}", text):
            cells.append((text, m.group(1)))
            start = m.end()
    cells.append((line[start:end.start()], end.group(1)))
    return cells


def is_heading(line: str, before_blank: bool, after: str) -> bool:
    words = line.split()
    return (before_blank and bool(after.strip()) and len(words) <= 4 and not re.search(r"\d", line)
            and not line.rstrip().endswith((",", ".")) and len(line) >= 4 and not NOT_A_DISH.search(line))


def parse_transcript(text: str, year: int) -> list[dict]:
    """Dishes found in one page's transcript, in reading order."""
    lines = [re.sub(r"[ \t]+$", "", raw) for raw in text.replace("\r", "").split("\n")]
    dishes: list[dict] = []
    heading = previous_heading = None
    pending: list[str] = []  # unpriced lines since the last blank line or dish
    last: dict | None = None  # the dish a following unpriced line would describe

    def add(name: str, price_token: str, description: str = "") -> dict | None:
        name = clean_name(re.sub(r"^\d+\.\s*", "", name))
        price = to_price(price_token, year)
        if price is None or not looks_like_dish(name) or SIZE_WORD.match(name) or NOT_A_DISH.search(name):
            return None
        dish = {"name": name, "description": clean_name(description)[:160], "heading": heading, "price": price}
        dishes.append(dish)
        return dish

    def close_block(block: list[str], token: str, tail: str = "") -> None:
        """A name line, lines of description, then the price: "PRESIDENTE COCKTAIL / recipe / .50"."""
        nonlocal heading
        if block[0] == (heading or "") or title_case(block[0]) == heading:
            heading = previous_heading  # that short line was the dish's name, not a section
        add(block[0], token, " ".join(block[1:] + [tail]))

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            pending, last = [], None
            continue
        before_blank = i == 0 or not lines[i - 1].strip()
        after = lines[i + 1] if i + 1 < len(lines) else ""
        cells = split_cells(stripped)
        if cells[0][1] is None:  # no price on this line
            if is_heading(stripped, before_blank, after):
                previous_heading, heading = heading, title_case(stripped) if stripped.isupper() else stripped
                pending, last = [stripped], None
            elif last is not None and not pending and not stripped.endswith(","):
                if len(last["description"]) < 160:
                    last["description"] = clean_name(f"{last['description']} {stripped}")[:160]
            else:
                pending.append(stripped)
            continue
        if len(cells) == 1 and not re.search(r"[A-Za-z]{3}", cells[0][0]):
            # a price alone on its line belongs to the block above it:
            # "PRESIDENTE COCKTAIL / recipe lines / .50" or "1. Shish Kebab / description / $9.95"
            numbered = [n for n, p in enumerate(pending) if re.match(r"^\d+\.\s*\S", p)]
            start = numbered[-1] if numbered else 0
            if pending[start:]:
                close_block(pending[start:], cells[0][1])
            pending, last = [], None
            continue
        if len(cells) == 1 and len(pending) >= 2 and pending[0].isupper():
            close_block(pending, cells[0][1], cells[0][0])  # the price ends the last line of the description
            pending, last = [], None
            continue
        prefix = " ".join(pending[-1:]) if pending and stripped[0].islower() else ""  # name wrapped onto two lines
        for n, (cell_text, token) in enumerate(cells):
            last = add(f"{prefix} {cell_text}" if n == 0 and prefix else cell_text, token) or last
        if len(cells) > 1:
            last = None  # a following line could belong to any of them
        pending = []
    return dishes


# ---------------------------------------------------------------------------
# Finding each dish on the page image
# ---------------------------------------------------------------------------
def ocr_words(image: Path) -> list[list[dict]]:
    """Words on the page grouped into text lines, via the tesseract program."""
    cache = image.with_suffix(".tsv")
    if not cache.exists():
        run = subprocess.run(["tesseract", str(image), "-", "--psm", "11", "tsv"], capture_output=True, text=True, check=True)
        cache.write_text(run.stdout)
    lines: dict[tuple, list[dict]] = {}
    for row in csv.DictReader(io.StringIO(cache.read_text()), delimiter="\t", quoting=csv.QUOTE_NONE):
        word = (row.get("text") or "").strip()
        if not word or float(row["conf"]) < 20:
            continue
        key = (row["block_num"], row["par_num"], row["line_num"])
        lines.setdefault(key, []).append({"t": re.sub(r"[^a-z0-9]", "", word.lower()), "x": int(row["left"]),
                                          "y": int(row["top"]), "w": int(row["width"]), "h": int(row["height"])})
    return [[w for w in line if w["t"]] for line in lines.values()]


def find_on_page(name: str, lines: list[list[dict]], used: set[tuple]) -> list[int] | None:
    """Pixel box [x, y, w, h] of the best match for a dish name among the OCR'd lines."""
    target = re.sub(r"[^a-z0-9 ]", "", name.lower()).split()[:6]
    if not target:
        return None
    wanted = "".join(target)
    best, best_score = None, 0.0
    for line in lines:
        for size in {len(target), len(target) - 1, len(target) + 1}:
            if size < 1:
                continue
            for start in range(0, max(len(line) - size, 0) + 1):
                window = line[start:start + size]
                if not window:
                    continue
                score = difflib.SequenceMatcher(None, wanted, "".join(w["t"] for w in window)).ratio()
                key = (window[0]["x"], window[0]["y"])
                if key in used:
                    score -= 0.08  # prefer a line no other dish has claimed
                if score > best_score:
                    best, best_score = window, score
    if best is None or best_score < 0.72:
        return None
    used.add((best[0]["x"], best[0]["y"]))
    x0, y0 = min(w["x"] for w in best), min(w["y"] for w in best)
    x1, y1 = max(w["x"] + w["w"] for w in best), max(w["y"] + w["h"] for w in best)
    pad = round((y1 - y0) * 0.35)
    return [max(x0 - pad, 0), max(y0 - pad, 0), x1 - x0 + 2 * pad, y1 - y0 + 2 * pad]


# ---------------------------------------------------------------------------
# Build entries
# ---------------------------------------------------------------------------
def fields_of(item: dict) -> dict[str, str]:
    return {f["key"]: str(f["value"]).strip().strip(";").strip() for f in item.get("fields", [])}


def scaled(width: float, height: float) -> tuple[int, int]:
    scale = min(IMAGE_MAX / width, IMAGE_MAX / height, 1)
    return round(width * scale), round(height * scale)


def build_entry(record: dict, max_dishes: int, do_locate: bool, geo_cache: dict, use_network: bool) -> dict | None:
    item = get_json(ITEM_API.format(id=record["pointer"]), f"item_{record['pointer']}.json")
    parent = item.get("parent") or {}
    meta = fields_of(parent if parent.get("fields") else item)
    children = parent.get("children") or []
    page_ids = [c["id"] for c in children] or [item["id"]]
    pages = [item if pid == item["id"] else get_json(ITEM_API.format(id=pid), f"item_{pid}.json") for pid in page_ids]
    full_text = "\n".join(p.get("text") or "" for p in pages)

    year_match = re.match(r"(\d{4})", meta.get("date", "")) or re.search(r"copyright\w*[^\d]{0,60}((?:18|19)\d{2})",
                                                                         full_text, re.IGNORECASE | re.DOTALL)
    if not year_match:
        print(f"  skip {record['pointer']}: no year ({meta.get('title')})", file=sys.stderr)
        return None
    year = int(year_match.group(1))
    title = meta.get("title", "")
    if EVENT_SKIP.search(title):
        return None

    restau = meta.get("restau", "").split(";")[0]
    raw_name = re.sub(r"\s*\(.*$", "", restau).strip() or title.split(",")[0]
    # "Coffee Shop (Palmer House : Chicago, Ill.)" is a room inside a larger house: say which
    house = re.search(r"\(([^:()]+?)\s*:\s*Chicago", restau)
    if house and house.group(1).strip().lower() not in {"restaurant", "resaurant", "firm", "hotel", "club", "bar"}:
        raw_name = f"{raw_name}, {house.group(1).strip()}"
    key = venue_key(f"{raw_name} {meta.get('restau', '')} {title}")
    known = KNOWN_VENUES.get(key or "", {})
    name = raw_name if house else known.get("name", raw_name)

    used_pages, dishes, seen = [], [], set()
    for page in pages:
        found = parse_transcript(page.get("text") or "", year)
        if not found or len(dishes) >= max_dishes:
            continue
        width, height = scaled(float(page["imageWidth"]), float(page["imageHeight"]))
        lines = None
        if do_locate:
            try:
                lines = ocr_words(get_image(page["id"]))
            except Exception as exc:  # the highlight is optional; the dish list is not
                print(f"    could not locate dishes on page {page['id']}: {exc}", file=sys.stderr)
        claimed: set[tuple] = set()
        page_index = len(used_pages)
        added = 0
        for dish in found:
            if (dish["name"].lower(), dish["price"]) in seen or len(dishes) >= max_dishes:
                continue
            seen.add((dish["name"].lower(), dish["price"]))
            guess = categorize(dish["name"])
            entry = {
                "id": f"cia-{record['pointer']}-{len(dishes) + 1}",
                "name": dish["name"],
                "description": dish["description"],
                # the menu's own section heading when it has one, else a keyword guess
                "category": dish["heading"] or guess,
                "price": dish["price"],
                "page": page_index,
            }
            box = find_on_page(dish["name"], lines, claimed) if lines else None
            if box:
                entry["bbox"] = box
            dishes.append(entry)
            added += 1
        if added:
            used_pages.append({
                "src": IMAGE_URL.format(id=page["id"], max=IMAGE_MAX),
                "width": width,
                "height": height,
                "sourceUrl": ITEM_URL.format(id=page["id"]),
            })
    if not dishes:
        return None
    if not any(d for d in dishes if d["category"] not in {categorize(d["name"])}):
        dishes = sort_menu(dishes)  # no headings in the transcript: use the usual menu order

    if "lat" in known:
        lat, lng, address, how = known["lat"], known["lng"], known["address"], "hand-entered"
    else:
        lat, lng, address, how = locate(meta.get("addres", ""), year, geo_cache, use_network)

    first = used_pages[0]
    number = meta.get("menu", "").replace("CIA ", "")
    return {
        "id": f"cia-{record['pointer']}",
        "venue": key or re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"),
        "name": name,
        "year": year,
        "opened": known.get("opened", year),
        "closed": known.get("closed", None if "opened" in known else year),
        "yearsKnown": "opened" in known,
        "address": address,
        "lat": lat,
        "lng": lng,
        "cuisine": known.get("cuisine", "Restaurant"),
        "emoji": known.get("emoji", "🍽️"),
        "blurb": known.get("blurb", re.split(r"(?<=\.)\s", meta.get("descri", ""))[0]),
        "stillStanding": {
            "status": known.get("status", "unknown"),
            "label": known.get("label", "Not yet researched"),
            "today": known.get("today", "Nobody has checked what stands at this address today."),
        },
        "scan": {
            **first,
            "placeholder": False,
            "credit": "The Culinary Institute of America, Conrad N. Hilton Library, Archives and Special Collections: "
                      f"CIA Menu Collection{', menu ' + number if number else ''}. Transcribed by the library.",
            "sourceUrl": ITEM_URL.format(id=record["pointer"]),
            "license": meta.get("rights") or "Rights not stated by the holding institution.",
        },
        "pages": used_pages,
        "source": "cia",
        "location": {"method": how},
        "menu": dishes,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--decades", nargs="+", default=["1930s", "1980s"], metavar="1930s")
    p.add_argument("--menus", type=Path, default=DEFAULT_MENUS)
    p.add_argument("--max-dishes", type=int, default=120)
    p.add_argument("--min-dishes", type=int, default=5)
    p.add_argument("--no-locate", action="store_true", help="do not OCR page images to place highlight boxes")
    p.add_argument("--no-geocode", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    DATA_DIR.mkdir(exist_ok=True)
    do_locate = not args.no_locate
    if do_locate and not shutil.which("tesseract"):
        print("tesseract not found: importing without highlight boxes", file=sys.stderr)
        do_locate = False
    geo_path = DATA_DIR / "geocode_cache.json"
    geo_cache = json.loads(geo_path.read_text()) if geo_path.exists() else {}

    entries = []
    for decade in args.decades:
        if not re.fullmatch(r"(18|19)\d0s", decade):
            p.error(f"not a decade: {decade}")
        result = get_json(QUERY_URL.format(decade=decade), f"query_{decade}.json")
        print(f"{decade}: {result['pager']['total']} Chicago records", file=sys.stderr)
        for record in result.get("records", []):
            entry = build_entry(record, args.max_dishes, do_locate, geo_cache, not args.no_geocode)
            if entry and len(entry["menu"]) >= args.min_dishes:
                boxed = sum("bbox" in d for d in entry["menu"])
                print(f"  {entry['year']} {entry['name']:<34.34} {len(entry['menu']):>3} dishes, {boxed:>3} located, "
                      f"{len(entry['pages'])} page(s)  [{entry['id']}]", file=sys.stderr)
                entries.append(entry)
            elif entry:
                print(f"  skip {entry['id']} ({entry['name']}): only {len(entry['menu'])} priced dishes", file=sys.stderr)
    geo_path.write_text(json.dumps(geo_cache, indent=1))

    # One menu per venue and year: the app shows a venue's menus by year, so a
    # second menu of the same year could never be reached. Keep the fullest,
    # and give way to a menu another source already has for that venue and year.
    doc = json.loads(args.menus.read_text())
    decades = {int(d[:4]) for d in args.decades}
    kept_others = [r for r in doc["restaurants"]
                   if not (r.get("source") == "cia" and r["year"] // 10 * 10 in decades)]
    taken = {(r.get("venue"), r["year"]) for r in kept_others}
    unique: dict[tuple, dict] = {}
    for entry in sorted(entries, key=lambda e: -len(e["menu"])):
        slot = (entry["venue"], entry["year"])
        if slot in taken or slot in unique:
            print(f"  drop {entry['id']} ({entry['year']} {entry['name']}): that venue and year is already covered",
                  file=sys.stderr)
            continue
        unique[slot] = entry
    entries = list(unique.values())

    if args.dry_run:
        return 0
    doc["restaurants"] = kept_others + entries
    doc["restaurants"].sort(key=lambda r: (r["year"], r["name"]))
    args.menus.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"wrote {args.menus}: {len(doc['restaurants'])} menus ({len(entries)} from the CIA)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
