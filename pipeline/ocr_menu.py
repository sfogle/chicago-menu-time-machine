#!/usr/bin/env python3
"""OCR a scanned menu and append it to the Time Machine dataset.

    python ocr_menu.py --image path/to/scan.jpg --restaurant "The Berghoff" \
        --year 1952 --address "17 W Adams St"

Pipeline:
  1. OCR the image into text fragments with pixel bounding boxes
     (PaddleOCR if installed, otherwise Tesseract via pytesseract).
  2. Cluster fragments into visual rows.
  3. Classify each row as a category header, a dish (name + price), or a
     description line belonging to the dish above it.
  4. Copy the scan into frontend/public/scans/ and append the structured
     entry to frontend/public/data/menus.json.

Run with --dry-run to print the parsed entry without touching any files.
OCR is never perfect on old menus: review the JSON afterwards.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import statistics
import sys
import unicodedata
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MENUS = REPO_ROOT / "frontend" / "public" / "data" / "menus.json"
DEFAULT_SCANS = REPO_ROOT / "frontend" / "public" / "scans"
LOOP = (41.8781, -87.6298)
TESS_WIDTH = 1600  # upscale narrower scans to this before Tesseract


@dataclass
class Fragment:
    """One piece of recognised text and its pixel box."""

    text: str
    x: int
    y: int
    w: int
    h: int
    conf: float  # 0-100

    @property
    def yc(self) -> float:
        return self.y + self.h / 2

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h


# ---------------------------------------------------------------------------
# OCR engines
# ---------------------------------------------------------------------------
_PADDLE: dict = {}


def ocr_paddle(image_path: Path) -> list[Fragment]:
    """PaddleOCR. Supports both the 2.x (`.ocr`) and 3.x (`.predict`) APIs."""
    from paddleocr import PaddleOCR  # noqa: PLC0415 (optional dependency)

    fragments: list[Fragment] = []

    def add(poly, text, score) -> None:
        xs = [float(p[0]) for p in poly]
        ys = [float(p[1]) for p in poly]
        if text and text.strip():
            fragments.append(Fragment(
                text.strip(), int(min(xs)), int(min(ys)),
                int(max(xs) - min(xs)), int(max(ys) - min(ys)), float(score) * 100,
            ))

    try:  # 3.x
        if "v3" not in _PADDLE:  # loading the models is slow; keep one engine per process
            _PADDLE["v3"] = PaddleOCR(
                lang="en",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
        engine = _PADDLE["v3"]
        for page in engine.predict(str(image_path)):
            data = page.json["res"] if hasattr(page, "json") else page
            polys = data.get("rec_polys") or data.get("dt_polys") or []
            for poly, text, score in zip(polys, data["rec_texts"], data["rec_scores"]):
                add(poly, text, score)
    except (TypeError, AttributeError, ValueError):  # 2.x signature
        engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        for page in engine.ocr(str(image_path), cls=True) or []:
            for poly, (text, score) in page or []:
                add(poly, text, score)
    return fragments


def ocr_tesseract(image_path: Path) -> list[Fragment]:
    """Tesseract via pytesseract. Needs the `tesseract` binary on PATH."""
    import pytesseract  # noqa: PLC0415 (optional dependency)
    from PIL import Image, ImageOps  # noqa: PLC0415

    img = ImageOps.autocontrast(ImageOps.grayscale(Image.open(image_path)))
    scale = 1.0
    if img.width < TESS_WIDTH:  # Tesseract likes roughly 300 dpi
        scale = TESS_WIDTH / img.width
        img = img.resize((TESS_WIDTH, round(img.height * scale)), Image.LANCZOS)

    # --psm 11 (sparse text) finds the far-right price column and mostly ignores
    # dot leaders, which block modes turn into "ccc eee" noise.
    data = pytesseract.image_to_data(img, config="--psm 11", output_type=pytesseract.Output.DICT)
    fragments = []
    for i, text in enumerate(data["text"]):
        conf = float(data["conf"][i])
        if not text.strip() or conf < 40 or JUNK_RE.match(text.strip()):
            continue
        fragments.append(Fragment(
            text.strip(),
            round(data["left"][i] / scale), round(data["top"][i] / scale),
            round(data["width"][i] / scale), round(data["height"][i] / scale),
            conf,
        ))
    return fragments


def run_ocr(image_path: Path, engine: str) -> tuple[list[Fragment], str]:
    """Return (fragments, engine_used). `auto` prefers Paddle, falls back to Tesseract."""
    order = {"auto": ["paddle", "tesseract"], "paddle": ["paddle"], "tesseract": ["tesseract"]}[engine]
    errors = []
    for name in order:
        try:
            fragments = ocr_paddle(image_path) if name == "paddle" else ocr_tesseract(image_path)
            return fragments, name
        except ImportError as exc:
            errors.append(f"{name}: not installed ({exc.name})")
        except Exception as exc:  # engine present but failed; try the next one
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
    raise SystemExit(
        "No OCR engine could run:\n  " + "\n  ".join(errors)
        + "\nInstall one with `pip install -r requirements.txt` "
        "(Tesseract also needs the system binary: `brew install tesseract`)."
    )


# ---------------------------------------------------------------------------
# Row clustering and menu heuristics
# ---------------------------------------------------------------------------
def cluster_rows(fragments: list[Fragment]) -> list[list[Fragment]]:
    """Group fragments whose vertical centres line up into left-to-right rows."""
    if not fragments:
        return []
    tolerance = statistics.median(f.h for f in fragments) * 0.6
    rows: list[list[Fragment]] = []
    for frag in sorted(fragments, key=lambda f: f.yc):
        if rows and abs(frag.yc - statistics.mean(f.yc for f in rows[-1])) <= tolerance:
            rows[-1].append(frag)
        else:
            rows.append([frag])
    return [sorted(row, key=lambda f: f.x) for row in rows]


# "1.25", "$1.25", ".45", "1,25" at the end of a row; or "35c" / "35¢"
PRICE_RE = re.compile(r"(?:\$\s?)?(\d{0,3})\s?[.,]\s?(\d{2})\s*$")
CENTS_RE = re.compile(r"(\d{1,2})\s?(?:¢|c|cts?\.?)\s*$", re.IGNORECASE)
# a bare number that dot leaders run into: "Soup . . . . 25"
BARE_RE = re.compile(r"[.·•_\s]{4,}(\d{1,3})\s*$")
LEADERS_RE = re.compile(r"(?:[.·•_…]\s*){2,}|[-–—]{3,}")
JUNK_RE = re.compile(r"^[.·•_…\-–—|~=]+$")  # fragments that are only leaders/rules
# "Smoked Sturgeon 25": words, then a bare price with no leaders. Old menus
# price in multiples of five cents, which keeps "Table 12" from matching.
INLINE_RE = re.compile(r"[A-Za-z][A-Za-z)\]'.,]*\s+(\d{1,3})\s*$")


def ends_with_price(text: str) -> bool:
    if PRICE_RE.search(text) or CENTS_RE.search(text) or BARE_RE.search(text):
        return True
    m = INLINE_RE.search(text)
    return bool(m) and int(m.group(1)) % 5 == 0 and int(m.group(1)) > 0


def split_cells(row: list[Fragment]) -> list[list[Fragment]]:
    """Split a visual row into cells, each ending at a price.

    Menus are often set in two or three columns, so one row can hold several
    "dish price" pairs. A single-column row comes back as one cell.
    """
    cells: list[list[Fragment]] = []
    current: list[Fragment] = []
    for frag in row:
        current.append(frag)
        if ends_with_price(" ".join(f.text for f in current)):
            cells.append(current)
            current = []
    if current:
        # trailing fragments with no price: leaders/noise after the last price
        # belong to it, otherwise they are an unpriced cell of their own
        if cells and not any(c.isalpha() for f in current for c in f.text):
            cells[-1].extend(current)
        else:
            cells.append(current)
    return cells


def split_price(row: list[Fragment]) -> tuple[str, float | None, bool]:
    """Split a row into (name text, price, is_bare).

    'Wiener Schnitzel .... 1.65' -> ('Wiener Schnitzel ....', 1.65, False).
    is_bare marks a price read as a plain integer ("45"), which happens when
    the menu prints cents without a decimal or OCR drops a leading ".". The
    caller decides whether that means cents or dollars.
    """
    text = " ".join(f.text for f in row)
    m = PRICE_RE.search(text)
    if m:
        return text[: m.start()], float(f"{m.group(1) or 0}.{m.group(2)}"), False
    m = CENTS_RE.search(text)
    if m:
        return text[: m.start()], int(m.group(1)) / 100, False
    m = BARE_RE.search(text)
    if m:
        return text[: m.start(1)], float(m.group(1)), True
    m = INLINE_RE.search(text)
    if m and int(m.group(1)) % 5 == 0 and int(m.group(1)) > 0:
        return text[: m.start(1)], float(m.group(1)), True
    # a lone number set well apart at the right-hand end of the row
    if len(row) >= 2 and re.fullmatch(r"\d{1,3}", row[-1].text):
        if row[-1].x - row[-2].right > 2 * row[-1].h:
            return " ".join(f.text for f in row[:-1]), float(row[-1].text), True
    return text, None, False


def clean_name(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)  # PaddleOCR emits full-width punctuation
    text = LEADERS_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .,:;-–—·•*|_'\"")


def is_header(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if len(letters) < 3 or len(text.split()) > 6:
        return False
    return sum(c.isupper() for c in letters) / len(letters) > 0.8


def bbox_of(fragments: list[Fragment]) -> list[int]:
    x0 = min(f.x for f in fragments)
    y0 = min(f.y for f in fragments)
    return [x0, y0, max(f.right for f in fragments) - x0, max(f.bottom for f in fragments) - y0]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def parse_menu(rows: list[list[Fragment]], year: int) -> list[dict]:
    """Turn OCR rows into dish records with category, price and bounding box."""
    dishes: list[dict] = []
    category = "Menu"
    last: dict | None = None  # most recent dish, for attaching descriptions

    # work cell by cell so multi-column rows give one dish per column
    cells: list[list[Fragment]] = []
    shared: list[bool] = []  # True when the cell shares its row with others
    for row in rows:
        parts = split_cells(row)
        cells.extend(parts)
        shared.extend([len(parts) > 1] * len(parts))
    rows = cells
    split = [split_price(row) for row in rows]
    # If any price on the page has a decimal point, a bare "45" is a ".45" whose
    # point was lost. Otherwise fall back on the era: before the 1960s menus
    # routinely printed cents as bare numbers.
    has_decimal = any(price is not None and not bare for _, price, bare in split)
    bare_is_cents = has_decimal or year < 1960

    for row, (name_part, price, bare), in_columns in zip(rows, split, shared):
        raw = " ".join(f.text for f in row)
        if bare and (bare_is_cents or price >= 100):
            price = price / 100
        name = clean_name(name_part)
        box = bbox_of(row)

        if price is not None and sum(c.isalpha() for c in name) >= 3:
            last = None if in_columns else {}
            dish = {
                "name": name,
                "description": "",
                "category": category,
                "price": round(price, 2),
                "bbox": box,
                "confidence": round(statistics.mean(f.conf for f in row), 1),
                "_frags": list(row),
            }
            dishes.append(dish)
            if last is not None:
                last = dish
            continue

        text = clean_name(raw)
        if is_header(text):
            category = text.title()
            last = None
            continue

        # A short unpriced line sitting directly under a dish is its description.
        if in_columns:
            last = None  # can't tell which column a stray line belongs to
        if last and sum(c.isalpha() for c in text) >= 3:
            prev = last["bbox"]
            gap = box[1] - (prev[1] + prev[3])
            if gap < box[3] * 1.2 and not last["description"]:
                last["description"] = text
                last["_frags"].extend(row)
                last["bbox"] = bbox_of(last["_frags"])

    seen: dict[str, int] = {}
    for dish in dishes:
        del dish["_frags"]
        base = slugify(dish["name"])
        seen[base] = seen.get(base, 0) + 1
        dish["_slug"] = base if seen[base] == 1 else f"{base}-{seen[base]}"
    return dishes


# ---------------------------------------------------------------------------
# Dataset I/O
# ---------------------------------------------------------------------------
def geocode(address: str) -> tuple[float, float] | None:
    """Look an address up with OpenStreetMap Nominatim (one request)."""
    query = urllib.parse.urlencode({"q": f"{address}, Chicago, IL", "format": "json", "limit": 1})
    req = urllib.request.Request(
        f"https://nominatim.openstreetmap.org/search?{query}",
        headers={"User-Agent": "chicago-menu-time-machine-pipeline"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            hits = json.load(resp)
        return (float(hits[0]["lat"]), float(hits[0]["lon"])) if hits else None
    except Exception as exc:
        print(f"warning: geocoding failed ({exc})", file=sys.stderr)
        return None


def build_entry(args: argparse.Namespace, dishes: list[dict], engine: str, size: tuple[int, int]) -> dict:
    entry_id = f"{slugify(args.restaurant)}-{args.year}"
    if args.lat is not None and args.lng is not None:
        lat, lng = args.lat, args.lng
    elif args.geocode and (hit := geocode(args.address)):
        lat, lng = hit
    else:
        lat, lng = LOOP
        print("warning: no --lat/--lng given; pinned to the centre of the Loop. "
              "Pass coordinates or --geocode.", file=sys.stderr)

    confidences = [d["confidence"] for d in dishes]
    return {
        "id": entry_id,
        "name": args.restaurant,
        "year": args.year,
        "opened": args.opened if args.opened is not None else args.year,
        "closed": args.closed,
        "address": args.address,
        "lat": round(lat, 5),
        "lng": round(lng, 5),
        "cuisine": args.cuisine,
        "emoji": "🍽️",
        "blurb": args.blurb,
        "stillStanding": {
            "status": "unknown",
            "label": "Not yet researched",
            "today": args.today or "Nobody has checked what stands at this address today.",
        },
        "scan": {
            "src": f"scans/{entry_id}{args.image.suffix.lower()}",
            "width": size[0],
            "height": size[1],
            "placeholder": False,
            "credit": args.credit,
        },
        "ocr": {
            "engine": engine,
            "meanConfidence": round(statistics.mean(confidences), 1) if confidences else None,
            "processed": dt.date.today().isoformat(),
        },
        "menu": [
            {
                "id": f"{entry_id}-{d['_slug']}",
                **{k: v for k, v in d.items() if k != "_slug"},
            }
            for d in dishes
        ],
    }


def save_entry(entry: dict, image: Path, menus_path: Path, scans_dir: Path, replace: bool) -> None:
    doc = {"version": 1, "restaurants": []}
    if menus_path.exists():
        doc = json.loads(menus_path.read_text())
    existing = [r for r in doc["restaurants"] if r["id"] == entry["id"]]
    if existing and not replace:
        raise SystemExit(
            f"{entry['id']} is already in {menus_path}. Re-run with --replace to overwrite it."
        )
    doc["restaurants"] = [r for r in doc["restaurants"] if r["id"] != entry["id"]] + [entry]
    doc["restaurants"].sort(key=lambda r: (r["year"], r["name"]))

    scans_dir.mkdir(parents=True, exist_ok=True)
    dest = scans_dir / Path(entry["scan"]["src"]).name
    if image.resolve() != dest.resolve():
        shutil.copyfile(image, dest)
    menus_path.parent.mkdir(parents=True, exist_ok=True)
    menus_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"copied scan -> {dest}", file=sys.stderr)
    print(f"{'replaced' if existing else 'appended'} {entry['id']} in {menus_path}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--image", type=Path, required=True, help="menu scan (jpg/png/tif)")
    p.add_argument("--restaurant", required=True, help="restaurant name")
    p.add_argument("--year", type=int, required=True, help="year the menu was printed")
    p.add_argument("--address", required=True, help="street address in Chicago")
    p.add_argument("--lat", type=float, help="latitude (skip to use --geocode or the Loop)")
    p.add_argument("--lng", type=float, help="longitude")
    p.add_argument("--geocode", action="store_true", help="look the address up via OpenStreetMap Nominatim")
    p.add_argument("--opened", type=int, help="year the restaurant opened (default: --year)")
    p.add_argument("--closed", type=int, help="year it closed (omit if still open)")
    p.add_argument("--cuisine", default="Restaurant")
    p.add_argument("--blurb", default="", help="one-sentence description for the card")
    p.add_argument("--today", default="", help="what occupies the address today")
    p.add_argument("--credit", default="", help="scan source, e.g. 'NYPL Buttolph Collection'")
    p.add_argument("--engine", choices=["auto", "paddle", "tesseract"], default="auto")
    p.add_argument("--menus", type=Path, default=DEFAULT_MENUS, help="menus.json to update")
    p.add_argument("--scans-dir", type=Path, default=DEFAULT_SCANS, help="where to copy the scan")
    p.add_argument("--replace", action="store_true", help="overwrite an existing entry with the same id")
    p.add_argument("--dry-run", action="store_true", help="print the entry as JSON; write nothing")
    args = p.parse_args(argv)

    if not args.image.is_file():
        p.error(f"image not found: {args.image}")

    from PIL import Image  # noqa: PLC0415

    with Image.open(args.image) as im:
        size = im.size

    fragments, engine = run_ocr(args.image, args.engine)
    rows = cluster_rows(fragments)
    dishes = parse_menu(rows, args.year)
    print(f"[{engine}] {len(fragments)} text fragments -> {len(rows)} rows -> {len(dishes)} priced dishes",
          file=sys.stderr)
    if not dishes:
        print("error: no dish/price pairs found. Is the scan legible and upright?", file=sys.stderr)
        return 1

    entry = build_entry(args, dishes, engine, size)
    for item in entry["menu"]:
        print(f"  {item['category']:<24.24} {item['name']:<40.40} {item['price']:>6.2f}  {item['bbox']}",
              file=sys.stderr)

    if args.dry_run:
        print(json.dumps(entry, indent=2, ensure_ascii=False))
    else:
        save_entry(entry, args.image, args.menus, args.scans_dir, args.replace)
    return 0


if __name__ == "__main__":
    sys.exit(main())
