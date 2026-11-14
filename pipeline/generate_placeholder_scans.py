#!/usr/bin/env python3
"""Generate the seed dataset and its placeholder menu "scans".

Renders one vintage-styled PNG per seed restaurant into
frontend/public/scans/ and writes the matching entries (with exact pixel
bounding boxes for every dish) into frontend/public/data/menus.json.

The dishes and prices are period-plausible reconstructions for demo purposes,
NOT transcriptions of surviving menus. Replace them with real scans via
ocr_menu.py. Entries in menus.json that are not part of the seed set (i.e. ones
you added with ocr_menu.py) are left untouched.

    python generate_placeholder_scans.py
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SCANS_DIR = ROOT / "frontend" / "public" / "scans"
MENUS_JSON = ROOT / "frontend" / "public" / "data" / "menus.json"

FONT_DIR = Path("/System/Library/Fonts/Supplemental")
FALLBACK_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "C:/Windows/Fonts/georgia.ttf",
]

# name -> (regular, bold, italic) font files, tried in order
FACES = {
    "georgia": ("Georgia.ttf", "Georgia Bold.ttf", "Georgia Italic.ttf"),
    "times": ("Times New Roman.ttf", "Times New Roman Bold.ttf", "Times New Roman Italic.ttf"),
    "courier": ("Courier New.ttf", "Courier New Bold.ttf", "Courier New Italic.ttf"),
}


def font(face: str, style: int, size: int) -> ImageFont.FreeTypeFont:
    """style: 0 regular, 1 bold, 2 italic."""
    candidates = [str(FONT_DIR / FACES[face][style])] + FALLBACK_FONTS
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# ---------------------------------------------------------------------------
# Seed data. Item tuples are (name, price, description).
# ---------------------------------------------------------------------------
SEED = [
    {
        "id": "palmer-house-1908",
        "name": "Palmer House",
        "year": 1908,
        "opened": 1871,
        "closed": None,
        "address": "17 E Monroe St",
        "lat": 41.8805,
        "lng": -87.6270,
        "cuisine": "Grand Hotel Dining",
        "emoji": "🏛️",
        "blurb": "Potter Palmer's showpiece hotel, where the dining room ran on silver service and Lake Superior whitefish.",
        "stillStanding": {
            "status": "open",
            "label": "Still standing",
            "today": "Palmer House, a Hilton Hotel. The 1908 building was replaced on the same site in the 1920s, and the hotel never closed.",
        },
        "style": {"face": "times", "paper": (238, 226, 198), "ink": (52, 38, 28), "accent": (120, 40, 30)},
        "heading": "BILL OF FARE",
        "menu": [
            ("Oysters and Relishes", [
                ("Blue Points on the Half Shell", 0.30, "Half dozen, on cracked ice"),
                ("Celery Hearts", 0.25, ""),
                ("Queen Olives", 0.20, ""),
            ]),
            ("Soups", [
                ("Green Turtle Soup", 0.40, "With sherry"),
                ("Consomme in Cup", 0.20, ""),
                ("Chicken Gumbo", 0.25, ""),
            ]),
            ("Fish", [
                ("Broiled Lake Superior Whitefish", 0.60, "Maitre d'hotel butter"),
                ("Planked Shad", 0.75, ""),
            ]),
            ("Roasts and Entrees", [
                ("Prime Ribs of Beef au Jus", 0.70, ""),
                ("Sirloin Steak", 1.25, "Broiled to order"),
                ("Spring Lamb with Mint Sauce", 0.75, ""),
                ("Chicken a la Maryland", 1.00, "Corn fritters and bacon"),
            ]),
            ("Desserts", [
                ("Vanilla Ice Cream", 0.20, ""),
                ("Apple Pie", 0.10, ""),
                ("Coffee, per pot", 0.15, ""),
            ]),
        ],
    },
    {
        "id": "henricis-1927",
        "name": "Henrici's",
        "year": 1927,
        "opened": 1868,
        "closed": 1962,
        "address": "67 W Randolph St",
        "lat": 41.8843,
        "lng": -87.6302,
        "cuisine": "Viennese Bakery & Restaurant",
        "emoji": "🥐",
        "blurb": "The Randolph Street institution of the theater district, famous for coffee with whipped cream and a strict no-orchestra policy.",
        "stillStanding": {
            "status": "gone",
            "label": "Demolished 1962",
            "today": "Richard J. Daley Center and its plaza, home of the Chicago Picasso.",
        },
        "style": {"face": "georgia", "paper": (240, 232, 210), "ink": (40, 44, 60), "accent": (30, 60, 110)},
        "heading": "NO ORCHESTRAL DIN",
        "menu": [
            ("Soups", [
                ("Chicken Okra Soup", 0.25, ""),
                ("Cream of Tomato", 0.20, ""),
            ]),
            ("Entrees", [
                ("Wiener Schnitzel", 0.85, "With lemon and anchovy"),
                ("Hungarian Goulash with Spaetzle", 0.70, ""),
                ("Corned Beef and Cabbage", 0.65, "Boiled potato"),
                ("Broiled Whitefish", 0.80, ""),
                ("Chicken Pot Pie", 0.75, "Baked to order"),
                ("Sirloin Steak Sandwich", 0.90, ""),
            ]),
            ("Sandwiches", [
                ("Ham and Swiss on Rye", 0.35, ""),
                ("Club Sandwich", 0.55, ""),
            ]),
            ("Pastry and Coffee", [
                ("Henrici Coffee Cake", 0.15, "From our own bakery"),
                ("Apple Strudel", 0.20, ""),
                ("German Pancake", 0.50, "Powdered sugar and lemon"),
                ("Coffee with Whipped Cream", 0.15, ""),
            ]),
        ],
    },
    {
        "id": "fritzels-1948",
        "name": "Fritzel's",
        "year": 1948,
        "opened": 1947,
        "closed": 1972,
        "address": "201 N State St",
        "lat": 41.8857,
        "lng": -87.6277,
        "cuisine": "Celebrity Supper Club",
        "emoji": "🍸",
        "blurb": "State and Lake's see-and-be-seen room, where columnists held court and the portions were as big as the names.",
        "stillStanding": {
            "status": "gone",
            "label": "Closed 1972",
            "today": "The restaurant is long gone. The State and Lake corner is Loop retail beside the State/Lake 'L' station.",
        },
        "style": {"face": "georgia", "paper": (243, 236, 220), "ink": (36, 36, 40), "accent": (150, 30, 40)},
        "heading": "STATE AT LAKE",
        "menu": [
            ("Appetizers", [
                ("Jumbo Shrimp Cocktail", 0.75, ""),
                ("Chopped Chicken Liver", 0.60, "With rye toast"),
                ("Marinated Herring", 0.55, ""),
            ]),
            ("Entrees", [
                ("Broiled Prime Sirloin Steak", 3.75, "Aged beef, French fried onions"),
                ("Roast Prime Ribs of Beef", 2.95, ""),
                ("Calf's Liver and Bacon", 1.95, ""),
                ("Broiled Lake Trout", 1.85, "Lemon butter"),
                ("Chicken in the Pot", 2.25, "Matzo ball and noodles"),
                ("Corned Beef Hash", 1.50, "With poached egg"),
            ]),
            ("Salads and Sandwiches", [
                ("Fritzel's Chef Salad", 1.25, ""),
                ("Hot Pastrami on Rye", 0.95, ""),
            ]),
            ("Desserts", [
                ("Cheesecake", 0.45, ""),
                ("Strawberry Shortcake", 0.50, ""),
                ("Coffee", 0.15, ""),
            ]),
        ],
    },
    {
        "id": "berghoff-1952",
        "name": "The Berghoff",
        "year": 1952,
        "opened": 1898,
        "closed": None,
        "address": "17 W Adams St",
        "lat": 41.8793,
        "lng": -87.6285,
        "cuisine": "German",
        "emoji": "🍺",
        "blurb": "Holder of Chicago's first post-Prohibition liquor license, pouring its own beer beside schnitzel and sauerbraten.",
        "stillStanding": {
            "status": "open",
            "label": "Still open",
            "today": "The Berghoff. Same address, same oak bar, still family run.",
        },
        "style": {"face": "times", "paper": (236, 228, 204), "ink": (44, 34, 24), "accent": (110, 60, 20)},
        "heading": "SINCE 1898",
        "menu": [
            ("Appetizers", [
                ("Herring in Sour Cream", 0.45, ""),
                ("Liver Dumpling Soup", 0.25, ""),
            ]),
            ("German Specialties", [
                ("Wiener Schnitzel", 1.65, "German fried potatoes"),
                ("Sauerbraten with Potato Pancake", 1.50, ""),
                ("Kassler Rippchen", 1.55, "Smoked pork loin, sauerkraut"),
                ("Bratwurst and Sauerkraut", 1.10, ""),
                ("Thuringer Sausage", 1.05, ""),
            ]),
            ("From the Lakes", [
                ("Broiled Whitefish", 1.45, ""),
                ("Fried Lake Perch", 1.35, "Tartar sauce"),
            ]),
            ("Side Dishes", [
                ("Creamed Spinach", 0.25, ""),
                ("German Fried Potatoes", 0.20, ""),
            ]),
            ("Dessert and Drinks", [
                ("Apple Strudel", 0.30, ""),
                ("Berghoff Beer, stein", 0.20, "Light or dark"),
                ("Berghoff Root Beer", 0.10, ""),
            ]),
        ],
    },
    {
        "id": "kon-tiki-ports-1966",
        "name": "Kon-Tiki Ports",
        "year": 1966,
        "opened": 1962,
        "closed": 1978,
        "address": "505 N Michigan Ave",
        "lat": 41.8911,
        "lng": -87.6238,
        "cuisine": "Polynesian / Tiki",
        "emoji": "🗿",
        "blurb": "A tiki fantasia inside the Sheraton-Chicago, with themed rooms named for Pacific ports and rum drinks to match.",
        "stillStanding": {
            "status": "gone",
            "label": "Closed late 1970s",
            "today": "InterContinental Chicago Magnificent Mile. The hotel remains, the tiki rooms do not.",
        },
        "style": {"face": "georgia", "paper": (236, 224, 190), "ink": (60, 40, 20), "accent": (20, 100, 90)},
        "heading": "SHERATON-CHICAGO HOTEL",
        "menu": [
            ("Pupus", [
                ("Egg Roll", 0.95, ""),
                ("Crab Rangoon", 1.25, ""),
                ("Barbecued Spareribs", 1.75, ""),
                ("Pupu Platter for Two", 3.50, "Served over a flaming hibachi"),
            ]),
            ("Entrees", [
                ("Mandarin Duck", 4.25, "Pressed, with plum sauce"),
                ("Lobster Cantonese", 4.95, ""),
                ("Sweet and Sour Pork", 3.25, ""),
                ("Beef Teriyaki", 4.50, ""),
                ("Chicken Almond", 3.25, ""),
                ("Polynesian Shrimp", 3.95, "Pineapple and green pepper"),
            ]),
            ("Exotic Drinks", [
                ("Mai Tai", 1.50, ""),
                ("Zombie", 1.75, "Limit two per guest"),
                ("Scorpion Bowl", 3.00, "For two or more"),
                ("Navy Grog", 1.50, ""),
            ]),
            ("Dessert", [
                ("Coconut Ice Cream", 0.60, ""),
            ]),
        ],
    },
    {
        "id": "millers-pub-1974",
        "name": "Miller's Pub",
        "year": 1974,
        "opened": 1935,
        "closed": None,
        "address": "23 E Adams St",
        "lat": 41.8795,
        "lng": -87.6262,
        "cuisine": "Tavern & Ribs",
        "emoji": "🍖",
        "blurb": "The Gallios brothers' late-night Loop tavern, wallpapered in celebrity photos and known for ribs and Tom and Jerrys.",
        "stillStanding": {
            "status": "moved",
            "label": "Moved around the corner",
            "today": "Miller's Pub relocated to 134 S Wabash Ave after a 1989 fire and is still open there.",
        },
        "style": {"face": "courier", "paper": (242, 238, 226), "ink": (30, 30, 30), "accent": (140, 30, 30)},
        "heading": "OPEN TILL 4 A.M.",
        "menu": [
            ("Starters", [
                ("French Onion Soup", 0.95, ""),
                ("Shrimp Cocktail", 2.25, ""),
                ("Greek Salad", 1.95, "Feta, olives, anchovy"),
            ]),
            ("House Specialties", [
                ("Barbecued Baby Back Ribs", 5.95, "Full slab, our famous sauce"),
                ("Broiled Lake Superior Whitefish", 4.75, ""),
                ("New York Strip Steak", 7.50, ""),
                ("Half Broiled Chicken", 3.95, ""),
                ("Corned Beef and Cabbage", 3.75, ""),
            ]),
            ("Sandwiches", [
                ("Pub Burger", 1.95, "Half pound, with fries"),
                ("Reuben", 2.25, ""),
                ("Prime Rib Sandwich", 3.25, ""),
            ]),
            ("Drinks and Dessert", [
                ("Tom and Jerry", 0.95, "In season"),
                ("Draft Beer", 0.60, ""),
                ("Cheesecake", 0.95, ""),
            ]),
        ],
    },
]

WIDTH = 1200
MARGIN = 130


def price_text(price: float) -> str:
    return f"{price:.2f}".lstrip("0") if price < 1 else f"{price:.2f}"


def text_w(draw: ImageDraw.ImageDraw, text: str, fnt) -> int:
    return int(draw.textlength(text, font=fnt))


def render(entry: dict) -> tuple[Image.Image, list[dict]]:
    style = entry["style"]
    face, paper, ink, accent = style["face"], style["paper"], style["ink"], style["accent"]
    rng = random.Random(entry["id"])

    f_title = font(face, 1, 84)
    f_sub = font(face, 0, 28)
    f_cat = font(face, 1, 34)
    f_item = font(face, 0, 34)
    f_desc = font(face, 2, 24)
    f_foot = font(face, 2, 22)

    row_h, desc_h, cat_h = 58, 34, 96
    n_items = sum(len(items) for _, items in entry["menu"])
    n_desc = sum(1 for _, items in entry["menu"] for it in items if it[2])
    body_h = len(entry["menu"]) * cat_h + n_items * row_h + n_desc * desc_h
    header_h, footer_h = 330, 150
    height = header_h + body_h + footer_h

    img = Image.new("RGB", (WIDTH, height), paper)
    draw = ImageDraw.Draw(img)

    # frame
    draw.rectangle([44, 44, WIDTH - 44, height - 44], outline=accent, width=5)
    draw.rectangle([58, 58, WIDTH - 58, height - 58], outline=accent, width=1)

    def centered(text: str, y: int, fnt, fill) -> None:
        draw.text(((WIDTH - text_w(draw, text, fnt)) // 2, y), text, font=fnt, fill=fill)

    centered(entry["heading"], 96, f_sub, accent)
    centered(entry["name"], 140, f_title, ink)
    centered(f"{entry['address']}  -  Chicago  -  {entry['year']}", 250, f_sub, ink)
    draw.line([MARGIN, 300, WIDTH - MARGIN, 300], fill=accent, width=2)
    draw.line([MARGIN, 306, WIDTH - MARGIN, 306], fill=accent, width=1)

    y = header_h
    items_out: list[dict] = []
    for category, items in entry["menu"]:
        label = category.upper()
        lw = text_w(draw, label, f_cat)
        cx = (WIDTH - lw) // 2
        draw.text((cx, y + 34), label, font=f_cat, fill=accent)
        mid = y + 34 + 20
        draw.line([MARGIN, mid, cx - 24, mid], fill=accent, width=1)
        draw.line([cx + lw + 24, mid, WIDTH - MARGIN, mid], fill=accent, width=1)
        y += cat_h
        for name, price, desc in items:
            top = y
            ptxt = price_text(price)
            pw = text_w(draw, ptxt, f_item)
            nw = text_w(draw, name, f_item)
            draw.text((MARGIN, y + 8), name, font=f_item, fill=ink)
            draw.text((WIDTH - MARGIN - pw, y + 8), ptxt, font=f_item, fill=ink)
            # dot leaders
            x = MARGIN + nw + 22
            while x < WIDTH - MARGIN - pw - 22:
                draw.ellipse([x, y + 36, x + 3, y + 39], fill=ink)
                x += 16
            y += row_h
            if desc:
                draw.text((MARGIN + 28, y - 6), desc, font=f_desc, fill=ink)
                y += desc_h
            items_out.append({
                "id": f"{entry['id']}-{slug(name)}",
                "name": name,
                "description": desc,
                "category": category,
                "price": price,
                "bbox": [MARGIN - 16, top, WIDTH - 2 * MARGIN + 32, y - top],
            })

    draw.line([MARGIN, y + 40, WIDTH - MARGIN, y + 40], fill=accent, width=1)
    centered("Placeholder scan generated for Chicago Menu Time Machine", y + 62, f_foot, ink)

    # paper ageing: a few soft stains, then a very light blur so it reads as a scan
    stains = Image.new("L", img.size, 0)
    sdraw = ImageDraw.Draw(stains)
    for _ in range(7):
        cx, cy = rng.randint(0, WIDTH), rng.randint(0, height)
        r = rng.randint(90, 260)
        sdraw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rng.randint(10, 26))
    stains = stains.filter(ImageFilter.GaussianBlur(70))
    img = Image.composite(Image.new("RGB", img.size, (150, 110, 60)), img, stains)
    img = img.filter(ImageFilter.GaussianBlur(0.4))
    return img, items_out


def main() -> None:
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    MENUS_JSON.parent.mkdir(parents=True, exist_ok=True)

    existing = []
    if MENUS_JSON.exists():
        existing = json.loads(MENUS_JSON.read_text()).get("restaurants", [])
    seed_ids = {e["id"] for e in SEED}
    restaurants = [r for r in existing if r["id"] not in seed_ids]

    for entry in SEED:
        img, items = render(entry)
        out = SCANS_DIR / f"{entry['id']}.png"
        img.save(out, optimize=True)
        record = {k: v for k, v in entry.items() if k not in ("style", "heading", "menu")}
        record["scan"] = {
            "src": f"scans/{out.name}",
            "width": img.width,
            "height": img.height,
            "placeholder": True,
            "credit": "Generated placeholder. Dishes and prices are period-plausible reconstructions, not a transcription.",
        }
        record["menu"] = items
        restaurants.append(record)
        print(f"  {out.name}: {img.width}x{img.height}, {len(items)} dishes")

    restaurants.sort(key=lambda r: (r["year"], r["name"]))
    MENUS_JSON.write_text(json.dumps({"version": 1, "restaurants": restaurants}, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {MENUS_JSON} ({len(restaurants)} restaurants)")


if __name__ == "__main__":
    main()
