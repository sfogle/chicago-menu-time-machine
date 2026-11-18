#!/usr/bin/env python3
"""Import Chicago menus from the NYPL "What's on the Menu?" open dataset.

    python import_nypl_chicago.py                    # rebuild the NYPL entries in menus.json
    python import_nypl_chicago.py --dry-run          # show what would be imported
    python import_nypl_chicago.py --validate-images  # also check each first-page image URL

The dataset is volunteer-transcribed, so there is no OCR step: dish names and
prices come straight from the CSVs, and each dish carries the normalised
(0-1) position a volunteer clicked on the page. Scan images are NOT
downloaded. menus.json stores NYPL image URLs and the app loads them from
NYPL's servers when a visitor opens a dish.

Steps:
  1. Download and unpack the bulk CSV archive (cached in pipeline/nypl_data/).
  2. Pick the Chicago menus: records whose place/location/sponsor says
     Chicago, plus a short list of later menus that have no city recorded but
     were confirmed as Chicago by reading the scan (CONFIRMED_CHICAGO).
  3. Join Menu -> MenuPage -> MenuItem -> Dish, clean names, assign categories.
  4. Locate each venue (hand-entered pins for known venues, otherwise
     OpenStreetMap Nominatim; pre-1909 street numbers are geocoded by street
     only, because Chicago renumbered its streets in 1909).
  5. Write compact entries to frontend/public/data/menus.json, replacing
     earlier "nypl-*" entries and leaving any others alone.

Standard library only, so it runs unchanged on Google Colab (see
nypl_colab.ipynb).
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sys
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from clean_menus import clean_name, categorize, looks_like_dish, sort_menu
from venues import KNOWN_VENUES, RAILROADS, railroad_key, standing, venue_key

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "nypl_data"
DEFAULT_MENUS = HERE.parent / "frontend" / "public" / "data" / "menus.json"

ARCHIVE_URL = "https://s3.amazonaws.com/menusdata.nypl.org/gzips/2021_08_01_07_01_17_data.tgz"
DATA_PAGE = "https://www.nypl.org/research/support/whats-on-the-menu"
USER_AGENT = "chicago-menu-time-machine-pipeline/0.1 (historical menu research script)"

IMAGE_WIDTH = 1000  # px. Never request /full/max/: be gentle with NYPL's image server.
IIIF_URL = "https://iiif.nypl.org/iiif/3/{image_id}/full/{width},/0/default.jpg"
FALLBACK_URL = "https://images.nypl.org/index.php?id={image_id}&t=w"
# The menus.nypl.org site the dataset came from has been retired (its menu pages
# return 404), so "view source" links go to the page's record in NYPL Digital
# Collections, using the uuid column of MenuPage.csv.
ITEM_URL = "https://digitalcollections.nypl.org/items/{uuid}"
NYPL_PAUSE = 0.5  # seconds between requests to NYPL
NOMINATIM_PAUSE = 1.1  # Nominatim's usage policy: at most one request per second
LOOP = (41.8781, -87.6298)

CHICAGO_RE = re.compile(r"chicago|chcago|chicao", re.IGNORECASE)
# one-off functions rather than a venue's regular bill of fare
EVENT_SKIP = re.compile(r"banquet|annual|anniversary|\bball\b|reunion|reception|tendered|wedding|charity", re.IGNORECASE)
# "Chicago" in the name of somewhere that is not in Chicago
NOT_CHICAGO = re.compile(r"new york & chicago limited|the chicago line|chicago club", re.IGNORECASE)

# Menus with no city in the dataset, confirmed as Chicago by reading the scan
# (a Chicago street address or "Chicago" printed on the menu). menu id -> note.
CONFIRMED_CHICAGO: dict[str, str] = {
    "30019": "Henrici's on Randolph, 1948: 'Chicago' and 'Randolph' printed on the menu",
    "28353": "Henrici's on Randolph, 1958: 'Chicago' printed on the menu",
    "28376": "Henrici's, 1958: Randolph and State Street printed on the menu",
    "30020": "Palmer House, 1948: 'Palmer House', 'Hiltonian' and the Merriel Abbott show printed on the menu",
    "28426": "The Red Star Inn, 1958: 'Clark St., Chicago' printed on the menu",
    "28934": "The Red Star Inn, 1962: 'Clark St., Chicago' printed on the menu",
    "29047": "Don the Beachcomber, 1963: 'Walton ... Chicago, Illinois' printed on the menu",
    # The next four rest on the venue's name and house dishes, not a printed address:
    "29162": "Fritzel's, 1950: name only (no city printed)",
    "29187": "The Drake, 1951: 'Drake' cocktails and Bookbinder soup, the Chicago Drake's signature",
    "30350": "Cape Cod Room, 1940: name only (the Drake's seafood room)",
    "26687": "Stock Yard Inn, 1971: catalogued under its Sirloin Room",
}


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------
def http_get(url: str, pause: float) -> bytes:
    time.sleep(pause)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def latest_archive_url() -> str:
    """Look for a newer .tgz link on NYPL's data page; fall back to the known one."""
    try:
        page = http_get(DATA_PAGE, NYPL_PAUSE).decode("utf-8", "replace")
        links = sorted(set(re.findall(r"https?://[\w./-]*menusdata\.nypl\.org/gzips/[\w.-]+\.tgz", page)))
        if links:
            return links[-1]  # file names start with a timestamp, so the last one is newest
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"  could not read {DATA_PAGE} ({exc}); using the known archive", file=sys.stderr)
    return ARCHIVE_URL


def ensure_data(data_dir: Path, check_latest: bool) -> None:
    needed = ["Menu.csv", "MenuPage.csv", "MenuItem.csv", "Dish.csv"]
    if all((data_dir / n).exists() for n in needed):
        return
    data_dir.mkdir(parents=True, exist_ok=True)
    url = latest_archive_url() if check_latest else ARCHIVE_URL
    archive = data_dir / "data.tgz"
    if not archive.exists():
        print(f"Downloading {url}", file=sys.stderr)
        archive.write_bytes(http_get(url, NYPL_PAUSE))
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            name = Path(member.name).name
            if member.isfile() and name in needed:  # extract only the four CSVs, flat, by base name
                member.name = name
                tar.extract(member, data_dir)
    missing = [n for n in needed if not (data_dir / n).exists()]
    if missing:
        raise SystemExit(f"archive did not contain {missing}")


def read_csv(path: Path):
    csv.field_size_limit(10**9)
    with open(path, newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------
def menu_year(menu: dict) -> int | None:
    m = re.match(r"(\d{4})", menu.get("date") or "")
    return int(m.group(1)) if m else None


def is_chicago(menu: dict) -> bool:
    if menu["id"] in CONFIRMED_CHICAGO:
        return True
    blob = " ".join(menu[k] for k in ("place", "location", "sponsor", "name"))
    return bool(CHICAGO_RE.search(blob)) and not NOT_CHICAGO.search(blob)


def display_name(menu: dict) -> str:
    raw = menu["location"] or menu["sponsor"] or menu["name"] or "Unknown venue"
    raw = re.sub(r"\s+", " ", raw).strip(' "[]')
    if raw.isupper():
        raw = raw.title().replace("'S", "'s")
    return raw


def street_address(menu: dict) -> str:
    """Street address out of the free-text place field, if it has one."""
    place = re.sub(r"[\[\]\"]", "", menu.get("place") or "")
    place = re.sub(r"[,;.\s]*\(?(chicago|chcago|chicao).*$", "", place, flags=re.IGNORECASE).strip(" ,;.")
    if re.search(r"\b(st|street|ave|avenue|blvd|boulevard|place|court|row)\b", place, re.IGNORECASE):
        return place.title().replace("Street", "St").replace("Avenue", "Ave")
    return ""


def price_ceiling(year: int) -> float:
    """Above this a 'price' is almost certainly a transcription slip."""
    return 8.0 if year < 1920 else 15.0 if year < 1950 else 40.0 if year < 1970 else 90.0


# ---------------------------------------------------------------------------
# Geocoding
# ---------------------------------------------------------------------------
def nominatim(query: str, cache: dict) -> tuple[float, float] | None:
    if query in cache:
        hit = cache[query]
        return tuple(hit) if hit else None
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": query, "format": "json", "limit": 1, "countrycodes": "us"})
    try:
        hits = json.loads(http_get(url, NOMINATIM_PAUSE))
        cache[query] = [round(float(hits[0]["lat"]), 5), round(float(hits[0]["lon"]), 5)] if hits else None
    except Exception as exc:  # network trouble must not sink the import
        print(f"    geocoding failed for {query!r}: {exc}", file=sys.stderr)
        return None
    hit = cache[query]
    return tuple(hit) if hit else None


def locate(address: str, year: int, cache: dict, use_network: bool) -> tuple[float, float, str, str]:
    """Return (lat, lng, address to display, how it was located)."""
    if not address:
        return LOOP[0], LOOP[1], "Chicago (address not recorded)", "default: centre of the Loop"
    numbered = re.match(r"^\s*[\d-]+\s+", address)
    if numbered and year < 1909:
        # Chicago renumbered its streets in 1909, so an 1900 "229 State St" is
        # not today's 229. Geocode the street alone and say so.
        street = address[numbered.end():]
        shown = f"{address} (pre-1909 numbering)"
        hit = nominatim(f"{street}, Loop, Chicago, Illinois", cache) if use_network else None
        if hit:
            return hit[0], hit[1], shown, "street only: pre-1909 numbering does not match today's"
        return LOOP[0], LOOP[1], shown, "default: centre of the Loop"
    hit = nominatim(f"{address}, Chicago, Illinois", cache) if use_network else None
    if hit:
        return hit[0], hit[1], address, "nominatim"
    return LOOP[0], LOOP[1], address, "default: centre of the Loop"


# ---------------------------------------------------------------------------
# Build entries
# ---------------------------------------------------------------------------
def build_entry(menu: dict, pages: list[dict], items: list[dict], dish_names: dict[str, str],
                max_dishes: int, geo_cache: dict, use_network: bool) -> dict | None:
    year = menu_year(menu)
    name = display_name(menu)
    ceiling = price_ceiling(year)

    # busiest pages first, then cap, so a 600-dish club bill of fare stays a manageable size
    by_page = collections.defaultdict(list)
    for it in items:
        by_page[it["menu_page_id"]].append(it)
    page_rows = sorted(pages, key=lambda p: -len(by_page[p["id"]]))
    used_pages: list[dict] = []
    dishes: list[dict] = []
    seen: set[tuple[str, float]] = set()
    for page in page_rows:
        if len(dishes) >= max_dishes or not by_page[page["id"]]:
            break
        if not (page["image_id"] and page["full_width"] and page["full_height"]):
            continue
        page_index = len(used_pages)
        added = 0
        for it in sorted(by_page[page["id"]], key=lambda i: (float(i["ypos"] or 0), float(i["xpos"] or 0))):
            try:
                price = round(float(it["price"]), 2)
                x, y = float(it["xpos"]), float(it["ypos"])
            except (TypeError, ValueError):
                continue
            dish = clean_name(dish_names.get(it["dish_id"], ""))
            if not (0 < price <= ceiling and 0 <= x <= 1 and 0 <= y <= 1 and looks_like_dish(dish)):
                continue
            if (dish.lower(), price) in seen:
                continue
            seen.add((dish.lower(), price))
            record = {
                "id": f"nypl-{menu['id']}-{it['id']}",
                "name": dish,
                "description": "",
                "category": categorize(dish),
                "price": price,
                "page": page_index,
                "pos": [round(x, 4), round(y, 4)],
            }
            dishes.append(record)
            added += 1
            if len(dishes) >= max_dishes:
                break
        if added:
            width = IMAGE_WIDTH
            height = round(IMAGE_WIDTH * int(page["full_height"]) / int(page["full_width"]))
            used_pages.append({
                "src": IIIF_URL.format(image_id=page["image_id"], width=IMAGE_WIDTH),
                "fallbackSrc": FALLBACK_URL.format(image_id=page["image_id"]),
                "width": width,
                "height": height,
                **({"sourceUrl": ITEM_URL.format(uuid=page["uuid"])} if page.get("uuid") else {}),
            })
    if not dishes:
        return None

    rail = railroad_key(name)
    known = RAILROADS[rail] if rail else KNOWN_VENUES.get(venue_key(name) or "", {})
    if "lat" in known:
        lat, lng, address, how = known["lat"], known["lng"], known["address"], "hand-entered"
    else:
        lat, lng, address, how = locate(street_address(menu), year, geo_cache, use_network)

    if rail:
        cuisine, emoji = "Railroad Dining Car", "🚂"
        blurb = "Not a restaurant: a railroad dining-car menu, pinned at the line's Chicago terminal."
        display = known["name"]
    else:
        cuisine, emoji = known.get("cuisine", "Restaurant"), known.get("emoji", "🍽️")
        blurb = known.get("blurb", "")
        # keep the source's own wording when it differs meaningfully (e.g. "Sheraton Blackstone Chicago")
        display = known.get("name", name) if year < 1960 or "name" not in known else name

    first = used_pages[0]
    return {
        "id": f"nypl-{menu['id']}",
        # shared by every menu of the same place, so the app can show one card per venue
        "venue": rail or venue_key(name) or re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"),
        "name": display,
        "year": year,
        "opened": known.get("opened", year),
        "closed": known.get("closed", None if "opened" in known else year),
        "yearsKnown": "opened" in known,
        "address": address,
        "lat": lat,
        "lng": lng,
        "cuisine": cuisine,
        "emoji": emoji,
        "blurb": blurb,
        "stillStanding": standing(known),
        "scan": {
            **first,
            "placeholder": False,
            "credit": "New York Public Library, Rare Book Division, via the What's on the Menu? project. "
                      "Transcribed by volunteers.",
            "sourceUrl": first.get("sourceUrl", "https://www.nypl.org/research/support/whats-on-the-menu"),
            "license": "Transcription data: CC0. Image served by NYPL.",
        },
        "pages": used_pages,
        "source": "nypl",
        "location": {"method": how},
        "menu": sort_menu(dishes),
    }


def head_ok(url: str) -> bool:
    """HEAD request (no image bytes transferred), rate limited."""
    time.sleep(NYPL_PAUSE)
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status == 200 and resp.headers.get_content_type().startswith("image/")
    except (urllib.error.URLError, TimeoutError):
        return False


def validate_images(entries: list[dict], cache: dict) -> None:
    """Make sure every page image is reachable.

    NYPL refuses the IIIF size we ask for (HTTP 403) on some later menus but
    still serves its standard web-size image, so those pages are switched to
    the fallback URL. The IIIF info.json answers 200 either way, so the image
    URL itself has to be checked.
    """
    for entry in entries:
        swapped = 0
        for page in entry["pages"]:
            # results are cached so re-runs do not ask NYPL the same question twice
            if page["src"] not in cache:
                cache[page["src"]] = head_ok(page["src"])
            if cache[page["src"]]:
                continue
            if page["fallbackSrc"] not in cache:
                cache[page["fallbackSrc"]] = head_ok(page["fallbackSrc"])
            if cache[page["fallbackSrc"]]:
                page["src"], page["fallbackSrc"] = page["fallbackSrc"], page["src"]
                swapped += 1
            else:
                print(f"    {entry['id']}: no reachable image for a page", file=sys.stderr)
        entry["scan"].update(src=entry["pages"][0]["src"], fallbackSrc=entry["pages"][0]["fallbackSrc"])
        if swapped:
            print(f"    {entry['id']} {entry['name']}: {swapped} page(s) use the web-size fallback image", file=sys.stderr)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data-dir", type=Path, default=DATA_DIR, help="where the CSVs are cached")
    p.add_argument("--menus", type=Path, default=DEFAULT_MENUS, help="menus.json to update")
    p.add_argument("--min-year", type=int, default=1890)
    p.add_argument("--max-year", type=int, default=1989)
    p.add_argument("--min-dishes", type=int, default=10, help="fewest priced dishes for a menu to count")
    p.add_argument("--max-dishes", type=int, default=120, help="cap per menu, to keep menus.json compact")
    p.add_argument("--max-menus", type=int, default=40)
    p.add_argument("--per-venue", type=int, default=2, help="most menus to keep for one venue")
    p.add_argument("--no-dining-cars", action="store_true", help="leave out railroad dining-car menus")
    p.add_argument("--no-geocode", action="store_true", help="never call Nominatim")
    p.add_argument("--check-latest", action="store_true", help="look on nypl.org for a newer archive first")
    p.add_argument("--validate-images", action="store_true", help="HEAD-check every page image; use the fallback URL where IIIF refuses")
    p.add_argument("--dry-run", action="store_true", help="print the selection; write nothing")
    args = p.parse_args()

    ensure_data(args.data_dir, args.check_latest)

    menus = {}
    for menu in read_csv(args.data_dir / "Menu.csv"):
        year = menu_year(menu)
        if year is None or not args.min_year <= year <= args.max_year or not is_chicago(menu):
            continue
        if menu["currency"] not in ("", "Dollars", "Cents"):
            continue
        if EVENT_SKIP.search(menu["event"] or "") and menu["id"] not in CONFIRMED_CHICAGO:
            continue
        if args.no_dining_cars and railroad_key(display_name(menu)):
            continue
        menus[menu["id"]] = menu
    print(f"{len(menus)} Chicago menus in range", file=sys.stderr)

    pages = collections.defaultdict(list)
    page_menu = {}
    for page in read_csv(args.data_dir / "MenuPage.csv"):
        if page["menu_id"] in menus:
            pages[page["menu_id"]].append(page)
            page_menu[page["id"]] = page["menu_id"]

    items = collections.defaultdict(list)
    wanted_dishes = set()
    for item in read_csv(args.data_dir / "MenuItem.csv"):
        menu_id = page_menu.get(item["menu_page_id"])
        if menu_id and item["price"] and item["dish_id"]:
            items[menu_id].append(item)
            wanted_dishes.add(item["dish_id"])
    dish_names = {d["id"]: d["name"] for d in read_csv(args.data_dir / "Dish.csv") if d["id"] in wanted_dishes}

    # one menu per venue per year (the dataset holds duplicate records), then a per-venue cap
    def venue_id(menu: dict) -> str:
        name = display_name(menu)
        return railroad_key(name) or venue_key(name) or re.sub(r"[^a-z]+", "", name.lower())

    best: dict[tuple[str, int], dict] = {}
    for menu in menus.values():
        if len(items[menu["id"]]) < args.min_dishes:
            continue
        key = (venue_id(menu), menu_year(menu))
        if key not in best or len(items[menu["id"]]) > len(items[best[key]["id"]]):
            best[key] = menu
    per_venue = collections.Counter()
    chosen = []
    # spread the choice across decades: round-robin by decade, biggest menus first
    by_decade = collections.defaultdict(list)
    for (vid, year), menu in best.items():
        by_decade[year // 10].append((vid, menu))
    for group in by_decade.values():
        group.sort(key=lambda vm: -len(items[vm[1]["id"]]))
    while len(chosen) < args.max_menus and any(by_decade.values()):
        for decade in sorted(by_decade):
            if by_decade[decade] and len(chosen) < args.max_menus:
                vid, menu = by_decade[decade].pop(0)
                if per_venue[vid] < args.per_venue:
                    per_venue[vid] += 1
                    chosen.append(menu)

    geo_cache_path = args.data_dir / "geocode_cache.json"
    geo_cache = json.loads(geo_cache_path.read_text()) if geo_cache_path.exists() else {}
    entries = []
    for menu in sorted(chosen, key=lambda m: (menu_year(m), display_name(m))):
        entry = build_entry(menu, pages[menu["id"]], items[menu["id"]], dish_names,
                            args.max_dishes, geo_cache, not args.no_geocode)
        if entry and len(entry["menu"]) >= args.min_dishes:
            entries.append(entry)
            print(f"  {entry['year']}  {entry['name']:<44.44} {len(entry['menu']):>4} dishes  "
                  f"{len(entry['pages'])} pg  [{entry['location']['method']}]", file=sys.stderr)
    geo_cache_path.write_text(json.dumps(geo_cache, indent=1))
    decades = sorted({e["year"] // 10 * 10 for e in entries})
    print(f"{len(entries)} menus across {', '.join(f'{d}s' for d in decades)}", file=sys.stderr)

    if args.validate_images:
        check_path = args.data_dir / "image_check_cache.json"
        checked = json.loads(check_path.read_text()) if check_path.exists() else {}
        validate_images(entries, checked)
        check_path.write_text(json.dumps(checked, indent=1))
    if args.dry_run:
        return 0

    doc = {"version": 2, "restaurants": []}
    if args.menus.exists():
        doc = json.loads(args.menus.read_text())
    others = [r for r in doc.get("restaurants", []) if not r["id"].startswith("nypl-")]
    doc = {"version": 2, "restaurants": sorted(others + entries, key=lambda r: (r["year"], r["name"]))}
    args.menus.parent.mkdir(parents=True, exist_ok=True)
    # compact separators: the file is data, not prose, and this roughly halves it
    args.menus.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"wrote {args.menus} ({len(doc['restaurants'])} restaurants, "
          f"{args.menus.stat().st_size // 1024} KB, {len(others)} non-NYPL entries kept)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
