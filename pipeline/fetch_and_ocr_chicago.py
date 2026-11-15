#!/usr/bin/env python3
"""Fetch real historical Chicago menu scans and OCR them into the dataset.

    python fetch_and_ocr_chicago.py            # fetch, OCR, pick the best 8-12
    python fetch_and_ocr_chicago.py --dry-run  # same, but write nothing to frontend/

Sources (both public APIs, no key needed):

  * Wikimedia Commons, category tree "Food menus from Chicago". These are
    almost all scans from the New York Public Library's Buttolph Collection of
    Menus, marked public domain.
  * Internet Archive advanced search for Chicago menu items that carry an
    explicit licence.

What it does:

  1. Lists candidate menus from both sources, with name, year, licence and
     credit, and skips banquets, club dinners and anything without a licence.
  2. Downloads up to --pages-per-menu page images per menu into
     pipeline/raw_scans/ (gitignored) and records them in manifest.json.
  3. Makes a compressed web copy of each page and OCRs it with ocr_menu.py.
     OCR results are cached in raw_scans/ocr_cache/, so re-runs are fast.
  4. Keeps the best page of each menu (most dish + price pairs), drops menus
     with too few priced dishes (table d'hote menus have no prices), and keeps
     the top --max-menus restaurants.
  5. Geocodes each address with OpenStreetMap Nominatim, writes the entries to
     frontend/public/data/menus.json, copies the web scans to
     frontend/public/scans/, and removes the generated placeholder entries.

Network etiquette: one request at a time, a pause between requests, and
back-off on HTTP 429.
"""
from __future__ import annotations

import argparse
import dataclasses
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

import ocr_menu

HERE = Path(__file__).resolve().parent
RAW_DIR = HERE / "raw_scans"
WEB_DIR = RAW_DIR / "web"
CACHE_DIR = RAW_DIR / "ocr_cache"
MANIFEST = RAW_DIR / "manifest.json"

USER_AGENT = "chicago-menu-time-machine-pipeline/0.1 (historical menu research script)"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
IA_SEARCH = "https://archive.org/advancedsearch.php"
IA_METADATA = "https://archive.org/metadata/"
PAUSE = 1.5  # seconds between requests

WEB_WIDTH = 1400  # px; published scans are downscaled to this width
WEB_QUALITY = 78
DOWNLOAD_WIDTH = 1920  # a standard Wikimedia thumbnail step

OK_LICENSES = re.compile(r"public domain|^pd\b|cc0|cc by|no restrictions|no known", re.IGNORECASE)
# events that are one-off banquets rather than a restaurant's own bill of fare
SKIP_EVENT = re.compile(
    r"BANQ|ANNUAL|REUNION|RECEPTION|COMPLIM|COMPL\.|TENDERED|WEDDING|MEETING|BALL\b|ANNIVERSARY|EXCURSION|"
    r"COLLATION|CONVENTION|IN HONOR|TESTIMONIAL| TO [A-Z]",
)
SKIP_SPONSOR = re.compile(r"CLUB|SOCIETY|ASSOCIATION|COMMITTEE|CITIZENS|BOARD OF|\?")


from venues import KNOWN_VENUES  # noqa: E402


@dataclasses.dataclass
class Candidate:
    """One menu (possibly several page images) from one source."""

    key: str  # stable id, e.g. "commons-273289" or "ia-1912-congress-..."
    venue: str
    year: int
    address: str  # as given by the source; may be empty
    credit: str
    license: str
    source_url: str
    page_urls: list[str]  # direct image URLs, in page order


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------
def http_get(url: str, tries: int = 6) -> bytes:
    for attempt in range(tries):
        time.sleep(PAUSE)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 503) or attempt == tries - 1:
                raise
            wait = int(exc.headers.get("Retry-After") or 15 * (attempt + 1))
            print(f"    rate limited, waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def get_json(base: str, **params) -> dict:
    return json.loads(http_get(f"{base}?{urllib.parse.urlencode(params, doseq=True)}"))


def strip_tags(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text or "")).strip()


# ---------------------------------------------------------------------------
# Source 1: Wikimedia Commons
# ---------------------------------------------------------------------------
# NYPL titles look like:
#   File:DINNER (held by) CAFE BRAUER (at) "229 STATE STREET, CHICAGO, IL" (REST') (NYPL Hades-272551-4000007695).jpg
NYPL_TITLE = re.compile(
    r"^File:(?P<event>.*?) \(held by\) (?P<sponsor>.*?) \(at\) (?P<place>.*) "
    r"\(+(?P<kind>[A-Z ]+)[^)]*\)+.*?\(NYPL Hades-(?P<menu>\d+)(?:-(?P<page>\d+))?\)\.jpe?g$",
    re.IGNORECASE,
)


def commons_candidates() -> list[Candidate]:
    pages: dict[str, dict] = {}
    cont: dict = {}
    while True:
        data = get_json(
            COMMONS_API, action="query", format="json", maxlag=5,
            generator="search", gsrnamespace=6, gsrlimit=50,
            gsrsearch='deepcategory:"Food menus from Chicago" filemime:image/jpeg',
            prop="imageinfo", iiprop="url|size|extmetadata", iiurlwidth=DOWNLOAD_WIDTH,
            iiextmetadatafilter="LicenseShortName|DateTimeOriginal|Credit", **cont,
        )
        for page in data.get("query", {}).get("pages", {}).values():
            if "imageinfo" in page:
                pages[page["title"]] = page["imageinfo"][0]
        if "continue" not in data:
            break
        cont = data["continue"]

    menus: dict[str, Candidate] = {}
    page_order: dict[str, list[tuple[int, str]]] = {}
    for title, info in pages.items():
        m = NYPL_TITLE.match(title)
        if not m:
            continue
        meta = info.get("extmetadata", {})
        license_name = strip_tags(meta.get("LicenseShortName", {}).get("value", ""))
        year_match = re.search(r"\b(1[89]\d\d)\b", strip_tags(meta.get("DateTimeOriginal", {}).get("value", "")))
        kind = m["kind"].upper()
        if not (year_match and OK_LICENSES.search(license_name)):
            continue
        if not kind.startswith(("REST", "HOT")):
            continue
        if SKIP_EVENT.search(m["event"].upper()) or SKIP_SPONSOR.search(m["sponsor"].upper()):
            continue
        place = m["place"].strip('"() ')
        address = re.sub(r",?\s*\(?CH[IC]*AGO.*$", "", place, flags=re.IGNORECASE).strip(' ,;"')
        key = f"commons-{m['menu']}"
        menus.setdefault(key, Candidate(
            key=key,
            venue=m["sponsor"].strip().title().replace("'S", "'s"),
            year=int(year_match.group(1)),
            address=address.title() if re.search(r"\d", address) or "ST" in address.upper() else "",
            credit="New York Public Library, Buttolph Collection of Menus, via Wikimedia Commons",
            license=license_name,
            source_url=info.get("descriptionurl", ""),
            page_urls=[],
        ))
        # the un-suffixed / 46xxxx-47xxxx ids are the catalogue's lead image; 4000… ids follow in page order
        page_order.setdefault(key, []).append((int(m["page"] or 0), info.get("thumburl") or info["url"]))

    for key, cand in menus.items():
        cand.page_urls = [url for _, url in sorted(page_order[key])]
    return list(menus.values())


# ---------------------------------------------------------------------------
# Source 2: Internet Archive
# ---------------------------------------------------------------------------
def ia_candidates(max_items: int) -> list[Candidate]:
    data = get_json(
        IA_SEARCH,
        q='title:(menu) AND title:(chicago) AND subject:(menu OR menus) AND mediatype:(texts) AND year:[1890 TO 1985]',
        **{"fl[]": ["identifier", "title", "year", "licenseurl", "creator"]},
        rows=100, output="json",
    )
    out: list[Candidate] = []
    for doc in data["response"]["docs"]:
        license_url = doc.get("licenseurl", "")
        title = doc.get("title", "")
        if not license_url or not doc.get("year"):
            continue  # no stated licence, or undated: leave it alone
        if re.search(r"athletic|club\b|association|program|unnamed|postcard|air lines", title, re.IGNORECASE) and \
                not re.search(r"grill", title, re.IGNORECASE):
            continue
        creator = doc.get("creator", "")
        venue = creator[0] if isinstance(creator, list) else creator
        if not venue:
            continue
        out.append(Candidate(
            key=f"ia-{doc['identifier']}",
            venue=venue,
            year=int(doc["year"]),
            address="",
            credit=f"Internet Archive item '{doc['identifier']}'",
            license=license_name_from_url(license_url),
            source_url=f"https://archive.org/details/{doc['identifier']}",
            page_urls=[],
        ))
    # fetch page counts only for the first few items of each venue
    per_venue: dict[str, int] = {}
    kept = []
    for cand in sorted(out, key=lambda c: (venue_key(c.venue), -c.year)):
        vk = venue_key(cand.venue)
        if per_venue.get(vk, 0) >= 2 or len(kept) >= max_items:
            continue
        per_venue[vk] = per_venue.get(vk, 0) + 1
        ident = cand.key[3:]
        meta = json.loads(http_get(IA_METADATA + ident))
        if not any(f.get("format") == "Single Page Processed JP2 ZIP" for f in meta.get("files", [])):
            continue
        desc = strip_tags(str(meta.get("metadata", {}).get("description", "")))
        addr = re.search(r"\b(\d{1,4} (?:[NSEW]\.? |North |South |East |West )?[A-Z][a-z]+(?: [A-Z][a-z]+)? (?:Ave|St|Blvd|Street|Avenue)\b\.?)", desc)
        cand.address = addr.group(1) if addr else ""
        n_pages = next((int(f.get("filecount", 0)) for f in meta["files"] if f.get("format") == "Single Page Processed JP2 ZIP"), 0) or 4
        cand.page_urls = [
            f"https://archive.org/download/{ident}/page/n{i}_w{DOWNLOAD_WIDTH}.jpg" for i in range(min(n_pages, 6))
        ]
        kept.append(cand)
    return kept


def license_name_from_url(url: str) -> str:
    m = re.search(r"creativecommons\.org/(licenses|publicdomain)/([a-z-]+)/([\d.]+)", url)
    if not m:
        return url
    return ("CC0 " if m[2] == "zero" else f"CC {m[2].upper()} ") + m[3]


# ---------------------------------------------------------------------------
# Download, OCR, select
# ---------------------------------------------------------------------------
def venue_key(name: str) -> str:
    name = name.lower().replace("lasalle", "la salle")
    for key in KNOWN_VENUES:
        if key in name:
            return key
    return re.sub(r"[^a-z0-9]+", "-", re.sub(r"\b(the|hotel|restaurant|cafe|and|&)\b", "", name)).strip("-")


def download_pages(cand: Candidate, limit: int) -> list[Path]:
    paths = []
    for i, url in enumerate(cand.page_urls[:limit]):
        dest = RAW_DIR / f"{cand.key}-p{i + 1}.jpg"
        if not dest.exists():
            try:
                blob = http_get(url)
            except urllib.error.HTTPError as exc:
                print(f"    page {i + 1}: HTTP {exc.code}, skipped", file=sys.stderr)
                if exc.code == 404:
                    break
                continue
            if not blob.startswith(b"\xff\xd8"):  # not a JPEG; never write unknown content
                print(f"    page {i + 1}: not a JPEG, skipped", file=sys.stderr)
                continue
            dest.write_bytes(blob)
        paths.append(dest)
    return paths


def web_copy(raw: Path) -> Path:
    """Downscaled, recompressed JPEG suitable for committing and serving."""
    dest = WEB_DIR / raw.name
    if not dest.exists():
        with Image.open(raw) as im:
            im = im.convert("RGB")
            if im.width > WEB_WIDTH:
                im = im.resize((WEB_WIDTH, round(im.height * WEB_WIDTH / im.width)), Image.LANCZOS)
            im.save(dest, "JPEG", quality=WEB_QUALITY, optimize=True, progressive=True)
    return dest


def ocr_cached(image: Path, engine: str) -> tuple[list[ocr_menu.Fragment], str]:
    cache = CACHE_DIR / f"{image.stem}.{engine}.json"
    if cache.exists():
        data = json.loads(cache.read_text())
        return [ocr_menu.Fragment(**f) for f in data["fragments"]], data["engine"]
    fragments, used = ocr_menu.run_ocr(image, engine)
    cache.write_text(json.dumps({"engine": used, "fragments": [dataclasses.asdict(f) for f in fragments]}))
    return fragments, used


CATEGORY_OK = re.compile(r"^[A-Za-z][A-Za-z ,&'-]{2,30}$")


def plausible(dishes: list[dict], year: int, venue: str = "") -> list[dict]:
    """Drop OCR rows that cannot be a dish at a price of the period, and
    reset category headings that are OCR noise or just the venue's name."""
    ceiling = 6.0 if year < 1930 else 25.0
    venue_words = set(re.findall(r"[a-z]{4,}", venue.lower()))
    keep = []
    for d in dishes:
        cat = d["category"]
        vowels = sum(c in "aeiou" for c in cat.lower())
        if (not CATEGORY_OK.match(cat) or vowels < len(cat) * 0.2 or "-" in cat and " " not in cat
                or venue_words & set(re.findall(r"[a-z]{4,}", cat.lower()))
                or not any(w in ocr_menu_words() for w in re.findall(r"[a-z]{3,}", cat.lower()))):
            d["category"] = "Menu"
        letters = sum(c.isalpha() for c in d["name"])
        if not (0.03 <= d["price"] <= ceiling) or letters < 4 or len(d["name"]) > 70:
            continue
        if letters / max(len(d["name"]), 1) < 0.6:
            continue
        keep.append(d)
    return keep


def ocr_menu_words() -> set[str]:
    """Words that plausibly appear in a menu section heading."""
    return {
        "soup", "soups", "fish", "oysters", "oyster", "clams", "shell", "relishes", "roast", "roasts", "entrees",
        "salad", "salads", "cold", "dishes", "meats", "vegetables", "eggs", "omelettes", "omelets", "dairy",
        "dessert", "desserts", "pastry", "sweets", "cheese", "fruit", "fruits", "ice", "creams", "cream", "coffee",
        "tea", "grill", "grilled", "broiled", "steaks", "chops", "game", "poultry", "sandwiches", "special",
        "specials", "ready", "order", "wines", "beer", "beers", "drinks", "beverages", "potatoes", "bread",
        "hors", "appetizers", "cocktails", "puddings", "pies", "cakes", "preserves", "lunch", "dinner", "supper",
    }


def geocode_or_known(cand: Candidate, known: dict, use_network: bool) -> tuple[float, float, str]:
    if "lat" in known:
        return known["lat"], known["lng"], "hand-entered"
    if cand.address and use_network:
        time.sleep(PAUSE)
        hit = ocr_menu.geocode(cand.address)
        if hit:
            return hit[0], hit[1], "nominatim"
    return ocr_menu.LOOP[0], ocr_menu.LOOP[1], "default (centre of the Loop)"


def build_entry(cand: Candidate, image: Path, dishes: list[dict], engine: str, use_network: bool) -> dict:
    known = KNOWN_VENUES.get(venue_key(cand.venue), {})
    lat, lng, how = geocode_or_known(cand, known, use_network)
    with Image.open(image) as im:
        size = im.size
    args = argparse.Namespace(
        restaurant=known.get("name", cand.venue),
        year=cand.year,
        address=known.get("address") or cand.address or "Chicago (address not recorded)",
        lat=lat, lng=lng, geocode=False,
        # years of operation are only filled in where they are known
        opened=known.get("opened", cand.year),
        closed=known.get("closed", None if "opened" in known else cand.year),
        cuisine=known.get("cuisine", "Restaurant"),
        blurb=known.get("blurb", ""),
        today=known.get("today", ""),
        credit=f"{cand.credit}. Licence: {cand.license}.",
        image=image,
    )
    entry = ocr_menu.build_entry(args, dishes, engine, size)
    entry["emoji"] = known.get("emoji", entry["emoji"])
    entry["yearsKnown"] = "opened" in known
    if "status" in known:
        entry["stillStanding"] = {"status": known["status"], "label": known["label"], "today": known["today"]}
    entry["scan"]["sourceUrl"] = cand.source_url
    entry["scan"]["license"] = cand.license
    entry["location"] = {"method": how}
    return entry


def remove_placeholders(menus_path: Path, scans_dir: Path) -> int:
    doc = json.loads(menus_path.read_text())
    gone = [r for r in doc["restaurants"] if r.get("scan", {}).get("placeholder")]
    doc["restaurants"] = [r for r in doc["restaurants"] if not r.get("scan", {}).get("placeholder")]
    for r in gone:
        (scans_dir / Path(r["scan"]["src"]).name).unlink(missing_ok=True)
    menus_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    return len(gone)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", choices=["auto", "paddle", "tesseract"], default="auto")
    p.add_argument("--max-menus", type=int, default=12, help="most restaurants to keep (default 12)")
    p.add_argument("--min-dishes", type=int, default=8, help="fewest priced dishes for a page to count")
    p.add_argument("--pages-per-menu", type=int, default=5, help="page images to try per menu")
    p.add_argument("--max-candidates", type=int, default=30, help="most menus to download and OCR")
    p.add_argument("--min-year", type=int, default=1890, help="skip menus older than this (the app starts at 1890)")
    p.add_argument("--max-year", type=int, default=1985)
    p.add_argument("--no-geocode", action="store_true", help="never call Nominatim")
    p.add_argument("--keep-placeholders", action="store_true", help="leave the generated seed entries in place")
    p.add_argument("--dry-run", action="store_true", help="download and OCR, but do not touch frontend/")
    p.add_argument("--menus", type=Path, default=ocr_menu.DEFAULT_MENUS)
    p.add_argument("--scans-dir", type=Path, default=ocr_menu.DEFAULT_SCANS)
    args = p.parse_args()

    for d in (RAW_DIR, WEB_DIR, CACHE_DIR):
        d.mkdir(parents=True, exist_ok=True)

    print("Listing candidates…", file=sys.stderr)
    commons = commons_candidates()
    print(f"  Wikimedia Commons: {len(commons)} priced-menu candidates", file=sys.stderr)
    archive = ia_candidates(max_items=10)
    print(f"  Internet Archive:  {len(archive)} candidates", file=sys.stderr)

    # one or two menus per venue, restaurants before hotels, newest first within a venue
    by_venue: dict[str, list[Candidate]] = {}
    for cand in commons + archive:
        if not args.min_year <= cand.year <= args.max_year:
            continue
        by_venue.setdefault(venue_key(cand.venue), []).append(cand)
    queue: list[Candidate] = []
    for vk, cands in by_venue.items():
        cands.sort(key=lambda c: -len(c.page_urls))
        queue.extend(cands[:2])
    queue.sort(key=lambda c: (venue_key(c.venue) not in KNOWN_VENUES, c.year))
    queue = queue[: args.max_candidates]

    manifest = []
    best: dict[str, tuple[int, Candidate, Path, list[dict], str]] = {}
    for n, cand in enumerate(queue, 1):
        print(f"[{n}/{len(queue)}] {cand.venue} ({cand.year}) {cand.key}", file=sys.stderr)
        for raw in download_pages(cand, args.pages_per_menu):
            web = web_copy(raw)
            fragments, engine = ocr_cached(web, args.engine)
            dishes = plausible(ocr_menu.parse_menu(ocr_menu.cluster_rows(fragments), cand.year), cand.year, cand.venue)
            print(f"    {raw.name}: {len(dishes)} priced dishes ({engine})", file=sys.stderr)
            manifest.append({
                "file": raw.name, "venue": cand.venue, "year": cand.year, "address": cand.address,
                "credit": cand.credit, "license": cand.license, "source": cand.source_url,
                "pricedDishes": len(dishes),
            })
            vk = venue_key(cand.venue)
            if len(dishes) >= args.min_dishes and len(dishes) > best.get(vk, (0,))[0]:
                best[vk] = (len(dishes), cand, web, dishes, engine)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")

    chosen = sorted(best.values(), key=lambda b: -b[0])[: args.max_menus]
    chosen.sort(key=lambda b: b[1].year)
    print(f"\nSelected {len(chosen)} menus:", file=sys.stderr)
    entries = []
    for count, cand, web, dishes, engine in chosen:
        entry = build_entry(cand, web, dishes, engine, use_network=not args.no_geocode)
        entries.append((entry, web))
        print(f"  {entry['year']}  {entry['name']:<34} {count:>3} dishes  {cand.license}  [{web.name}]", file=sys.stderr)

    if args.dry_run:
        print("\n--dry-run: nothing written to frontend/", file=sys.stderr)
        return 0
    if len(entries) < 8:
        print(f"\nOnly {len(entries)} usable menus (wanted at least 8); writing them anyway.", file=sys.stderr)
    for entry, web in entries:
        ocr_menu.save_entry(entry, web, args.menus, args.scans_dir, replace=True)
    if not args.keep_placeholders:
        print(f"removed {remove_placeholders(args.menus, args.scans_dir)} placeholder entries", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
