#!/usr/bin/env python3
"""Tidy dish names and assign menu categories.

Used two ways:

  * imported by import_nypl_chicago.py (clean_name, categorize, sort_menu)
  * run on its own to clean entries already in menus.json, e.g. ones added by
    ocr_menu.py, whose names carry OCR noise and whose categories are whatever
    heading the OCR happened to read:

        python clean_menus.py                 # clean every entry in place
        python clean_menus.py --only ocr      # only entries that came from OCR
        python clean_menus.py --dry-run       # report, change nothing

Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_MENUS = Path(__file__).resolve().parent.parent / "frontend" / "public" / "data" / "menus.json"

# Matching order: a dish goes to the first category whose pattern matches its
# name, so the more specific kinds of dish come first (a "clam chowder" is a
# soup, a "cheese sandwich" a sandwich). Display order is DISPLAY_ORDER below.
CATEGORIES: list[tuple[str, str]] = [
    ("Soups", r"\b(soups?|consomm\w*|bouillon|broth|chowder|bisque|gumbo|mulligatawny|pur[eé]e|potage|mock turtle|"
              r"green turtle|okra|julienne|cream of|vichyssoise|borscht|minestrone)\b"),
    ("Sandwiches", r"\b(sandwich\w*|club house|hamburger|burger|frankfurter|hot dog|reuben|on rye|on toast)\b"),
    ("Eggs & Omelettes", r"\b(eggs?|omelett?es?|scrambled|poached|shirred)\b"),
    ("Salads", r"\b(salads?|mayonnaise|lettuce|romaine|endive|slaw|waldorf|chicory|watercress|escarole)\b"),
    ("Oysters & Shellfish", r"\b(oysters?|blue ?points?|rockaways?|cotuits?|lynnhavens?|shrewsbur\w+|malpecques?|"
                            r"clams?|little necks?|cherry ?stones?|lobsters?|crabs?|crab ?meat|shrimps?|scallops?|"
                            r"mussels?|crawfish|prawns?)\b"),
    ("Fish", r"\b(fish|whitefish|trout|salmon|bass|pike|pickerel|perch|halibut|sole|flounder|mackerel|shad|roe|"
             r"smelts?|cod|codfish|haddock|finnan haddie|sturgeon|bluefish|pompano|snapper|turbot|kingfish|eel|"
             r"frogs?|frog legs|terrapin|red snapper|tuna|swordfish|scrod)\b"),
    ("Steaks, Chops & Grill", r"\b(steaks?|sirloin|porterhouse|tenderloin|filet|fillet mignon|chops?|cutlets?|"
                              r"grill\w*|broiled|planked|chateaubriand|t.bone|minute steak|mixed grill|ribs)\b"),
    ("Poultry & Game", r"\b(chicken|capon|turkey|duck\w*|goose|squab|pigeon|guinea|pheasant|partridge|quail|plover|"
                       r"snipe|grouse|venison|rabbit|hare|mallard|teal|canvas.?back|woodcock|game)\b"),
    ("Roasts & Entrées", r"\b(roast\w*|beef|veal|lamb|mutton|pork|ham|bacon|sausages?|liver|kidneys?|sweetbreads?|"
                         r"tongue|tripe|brains?|goulash|stew|hash|ragout|fricassee|pot pie|pie, |corned|schnitzel|"
                         r"sauerbraten|bratwurst|wiener|knackwurst|pigs?.? ?(feet|knuckles?)|ox ?tail|meat|curry|"
                         r"spaghetti|macaroni|ravioli|noodles?|chop suey|chow mein|teriyaki|cantonese|rarebit|"
                         r"welsh rabbit|croquettes?|entr[eé]e|braised|boiled dinner|short ?ribs|calf'?s?)\b"),
    ("Relishes & Appetizers", r"\b(olives?|celery|radish\w*|pickles?|gherkins?|chow.chow|caviar\w*|anchov\w+|sardines?|"
                              r"canap\w+|hors d|relish\w*|pate|p[aâ]t[eé]|foie gras|antipasto|herring|egg roll|"
                              r"rangoon|pupu|spareribs?|appetizer)\b"),
    ("Desserts & Fruit", r"\b(ice ?cream|ices?|sherbets?|sorbet|parfait|pudding|pies?|cakes?|shortcake|tarts?|"
                         r"pastry|pastries|eclairs?|strudel|custard|jelly|jellies|blanc.?mange|charlotte|meringue|"
                         r"souffl\w+|compote|preserve\w*|marmalade|jam|honey|waffles?|pancakes?|griddle|crullers?|"
                         r"doughnuts?|cookies?|macaroons?|lady ?fingers|biscuit tortoni|nesselrode|bavarian|mousse|"
                         r"sundae|fruit|apples?|oranges?|grape ?fruit|bananas?|berries|strawberr\w+|raspberr\w+|"
                         r"peach\w*|pears?|plums?|prunes?|figs?|dates|melon|cantaloupe|pineapple|grapes|cherries|"
                         r"nuts|raisins|bon ?bons|candy|candies|caramels?|chocolates|dessert)\b"),
    ("Cheese", r"\b(cheese|camembert|roquefort|brie|swiss|edam|stilton|gorgonzola|neufchatel|cheddar|limburger|"
               r"gruy[eè]re|liederkranz|american, |cream cheese|parmesan|port du salut)\b"),
    ("Vegetables & Sides", r"\b(potato\w*|pommes|asparagus|peas|beans?|spinach|corn|tomato\w*|cabbage|sauerkraut|"
                           r"cauliflower|carrots?|beets?|turnips?|onions?|mushrooms?|artichokes?|squash|egg ?plant|"
                           r"succotash|rice|hominy|parsnips?|brussels?|sprouts|kale|okra|peppers?|cucumbers?|"
                           r"vegetables?|toast|rolls?|bread|muffins?|biscuits?|crackers|zwieback|wafers)\b"),
    ("Drinks", r"\b(coffee|tea|cocoa|chocolate, |milk|buttermilk|cider|lemonade|ginger ale|mineral water|apollinaris|"
               r"vichy|lithia|water|beer|ale|stout|porter|pilsner|lager|wine|claret|champagne|sherry|port|burgundy|"
               r"sauterne|chablis|rhine|moselle|whiskey|whisky|bourbon|rye|scotch|gin|rum|brandy|cognac|cordial|"
               r"cocktail|highball|martini|manhattan|fizz|punch|zombie|mai tai|grog|daiquiri|liqueur|vermouth|"
               r"sarsaparilla|root beer|soda|coca.cola|postum|malted|kumyss|bottle|pint|quart|split|demi.tasse)\b"),
]
_COMPILED = [(name, re.compile(pattern, re.IGNORECASE)) for name, pattern in CATEGORIES]
OTHER = "Other Dishes"
ORDER = {name: i for i, (name, _) in enumerate(CATEGORIES)}
ORDER[OTHER] = len(ORDER)
# Shown first on the page even though they are matched late or early above.
DISPLAY_ORDER = [
    "Oysters & Shellfish", "Relishes & Appetizers", "Soups", "Fish", "Steaks, Chops & Grill", "Roasts & Entrées",
    "Poultry & Game", "Eggs & Omelettes", "Sandwiches", "Salads", "Vegetables & Sides", "Cheese", "Desserts & Fruit",
    "Drinks", OTHER,
]

SMALL_WORDS = {"a", "à", "a la", "la", "le", "au", "aux", "en", "de", "du", "des", "of", "and", "or", "with", "in",
               "on", "the", "to", "per", "for", "et", "sur", "half", "doz"}


def clean_name(name: str) -> str:
    """Normalise whitespace, punctuation and case in a dish name."""
    name = re.sub(r"\s+", " ", name or "").strip()
    name = re.sub(r"\s+([,.;:)])", r"\1", name)  # "Chicken , rice" -> "Chicken, rice"
    name = re.sub(r"([,;])(?=[A-Za-z])", r"\1 ", name)  # "Shrewsbury,halfdoz" -> "Shrewsbury, halfdoz"
    name = re.sub(r"\(\s+", "(", name)
    name = name.strip(" .,;:-–—*|_\"'[]")
    name = re.sub(r"^[\d.]+\s+(?=[A-Za-z])", "", name)  # leading stray numbers
    if name.count("(") != name.count(")"):
        name = name.replace("(", "").replace(")", "")
    letters = [c for c in name if c.isalpha()]
    if letters and sum(c.isupper() for c in letters) / len(letters) > 0.7:
        name = title_case(name)
    elif name and name[0].islower():
        name = name[0].upper() + name[1:]
    return name


def title_case(text: str) -> str:
    words = text.lower().split(" ")
    out = []
    for i, word in enumerate(words):
        bare = word.strip(",;:()")
        if i and bare in SMALL_WORDS:
            out.append(word)
        else:
            out.append(re.sub(r"[a-zà-ÿ]", lambda m: m.group(0).upper(), word, count=1))
    return " ".join(out)


def looks_like_dish(name: str) -> bool:
    letters = sum(c.isalpha() for c in name)
    return letters >= 3 and len(name) <= 80 and letters / max(len(name), 1) >= 0.55


def categorize(name: str) -> str:
    for category, pattern in _COMPILED:
        if pattern.search(name):
            return category
    return OTHER


def sort_menu(dishes: list[dict]) -> list[dict]:
    """Group dishes by category in menu order; keep source order within one."""
    rank = {name: i for i, name in enumerate(DISPLAY_ORDER)}
    return sorted(dishes, key=lambda d: rank.get(d["category"], len(rank)))


def clean_entry(entry: dict) -> tuple[int, int]:
    """Clean one restaurant entry in place. Returns (dishes kept, dishes dropped)."""
    kept, seen = [], set()
    for dish in entry.get("menu", []):
        name = clean_name(dish.get("name", ""))
        key = (name.lower(), dish.get("price"))
        if not looks_like_dish(name) or key in seen:
            continue
        seen.add(key)
        dish["name"] = name
        dish["description"] = clean_name(dish.get("description", ""))
        dish["category"] = categorize(name)
        kept.append(dish)
    dropped = len(entry.get("menu", [])) - len(kept)
    entry["menu"] = sort_menu(kept)
    return len(kept), dropped


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--menus", type=Path, default=DEFAULT_MENUS)
    p.add_argument("--only", choices=["all", "ocr"], default="all", help="'ocr' = entries with an 'ocr' block")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    doc = json.loads(args.menus.read_text())
    for entry in doc["restaurants"]:
        if args.only == "ocr" and "ocr" not in entry:
            continue
        kept, dropped = clean_entry(entry)
        cats = len({d["category"] for d in entry["menu"]})
        print(f"  {entry['year']} {entry['name']:<36.36} {kept:>4} dishes, {dropped:>3} dropped, {cats} categories",
              file=sys.stderr)
    if not args.dry_run:
        args.menus.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n")
        print(f"wrote {args.menus}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
