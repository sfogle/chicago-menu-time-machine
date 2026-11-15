"""What is known about specific Chicago venues.

The source datasets give a venue name and a year. Everything else here
(modern-equivalent address, map pin, years of operation, what stands there
today) is hand-entered from general reference knowledge and should be checked
before being relied on. Pre-1909 street numbers do not match today's numbering,
so those pins are approximate.

Keys are lower-case substrings matched against the venue name; more specific
keys must come before more general ones ("cape cod room" before "drake").
"""
from __future__ import annotations

KNOWN_VENUES: dict[str, dict] = {
    "blackstone": {
        "name": "The Blackstone Hotel", "address": "636 S Michigan Ave", "lat": 41.8734, "lng": -87.6244,
        "opened": 1910, "closed": None, "cuisine": "Hotel Grill", "emoji": "🎩",
        "blurb": "The 'Hotel of Presidents' on Michigan Avenue, new in 1910 and built to impress.",
        "status": "open", "label": "Still standing", "today": "The Blackstone, still operating as a hotel in the same building.",
    },
    "congress": {
        "name": "Congress Hotel and Annex", "address": "520 S Michigan Ave", "lat": 41.8753, "lng": -87.6246,
        "opened": 1893, "closed": None, "cuisine": "Hotel Dining Room", "emoji": "🏨",
        "blurb": "Built as the Auditorium Annex for the 1893 World's Fair crowds, facing Grant Park.",
        "status": "open", "label": "Still standing", "today": "The Congress Plaza Hotel, same building.",
    },
    "la salle": {
        "name": "Hotel La Salle", "address": "La Salle St & Madison St", "lat": 41.8821, "lng": -87.6327,
        "opened": 1909, "closed": 1976, "cuisine": "Hotel Dining Room", "emoji": "🏨",
        "blurb": "A 22-storey Loop hotel that billed itself as the finest west of New York.",
        "status": "gone", "label": "Demolished 1976", "today": "An office tower, Two North LaSalle, stands on the site.",
    },
    "lexington": {
        "name": "Lexington Hotel", "address": "Michigan Ave & 22nd St (Cermak Rd)", "lat": 41.8530, "lng": -87.6238,
        "opened": 1892, "closed": 1980, "cuisine": "Hotel Dining Room", "emoji": "🏨",
        "blurb": "A South Side hotel put up for the 1893 fair, later notorious as Al Capone's headquarters.",
        "status": "gone", "label": "Demolished 1995", "today": "The building was torn down in 1995; the corner has since been redeveloped.",
    },
    "sherman house": {
        "name": "Sherman House", "address": "Clark St & Randolph St", "lat": 41.8846, "lng": -87.6312,
        "opened": 1837, "closed": 1973, "cuisine": "Hotel Dining Room", "emoji": "🏨",
        "blurb": "One of Chicago's oldest hotel names, rebuilt several times on the same Loop corner.",
        "status": "gone", "label": "Demolished 1973", "today": "The James R. Thompson Center site.",
    },
    "chicago beach": {
        "name": "Chicago Beach Hotel", "address": "Hyde Park Blvd & Lake Michigan", "lat": 41.8024, "lng": -87.5838,
        "opened": 1892, "closed": 1927, "cuisine": "Resort Hotel", "emoji": "🏖️",
        "blurb": "A lakefront resort hotel in Hyde Park, opened in time for the 1893 World's Fair.",
        "status": "gone", "label": "Demolished", "today": "Residential towers in the Indian Village part of Hyde Park-Kenwood.",
    },
    "gunther": {
        "name": "Gunther's Confectionery", "address": "State St near Adams St", "lat": 41.8796, "lng": -87.6277,
        "cuisine": "Confectionery & Lunch Room", "emoji": "🍬",
        "blurb": "Candy maker C. F. Gunther's State Street shop, as famous for its curiosity museum as its caramels.",
        "status": "gone", "label": "Long gone", "today": "State Street retail. Exact modern lot not verified.",
    },
    "pabst": {
        "name": "Pabst Blue Ribbon Restaurant", "address": "122-124 S Clark St (pre-1909 numbering)", "lat": 41.8803, "lng": -87.6308,
        "cuisine": "German Beer Hall", "emoji": "🍺",
        "blurb": "A brewery-backed Loop restaurant, one of many tied houses the Milwaukee brewers ran in Chicago.",
        "status": "gone", "label": "Long gone", "today": "Loop office buildings. Pre-1909 street number, so the pin is approximate.",
    },
    "german restaurant": {
        "name": "German Restaurant & Buffet", "address": "137 E Madison St (pre-1909 numbering)", "lat": 41.8820, "lng": -87.6300,
        "cuisine": "German", "emoji": "🥨",
        "blurb": "A businessman's lunch room on Madison Street with a long daily card.",
        "status": "gone", "label": "Long gone", "today": "Loop office buildings. Pre-1909 street number, so the pin is approximate.",
    },
    "brauer": {
        "name": "Cafe Brauer", "address": "229 State St (pre-1909 numbering)", "lat": 41.8790, "lng": -87.6278,
        "cuisine": "Cafe & Restaurant", "emoji": "☕",
        "blurb": "The Brauer family's downtown cafe; they later ran the Lincoln Park refectory that still bears the name.",
        "status": "gone", "label": "Long gone", "today": "State Street retail. Pre-1909 street number, so the pin is approximate.",
    },
    "mangler": {
        "name": "Mangler's", "address": "La Salle St", "lat": 41.8815, "lng": -87.6324,
        "cuisine": "Restaurant", "emoji": "🍽️",
        "blurb": "A La Salle Street restaurant in the financial district.",
        "status": "unknown", "label": "Not yet researched", "today": "Only the street is recorded, so the pin marks La Salle Street generally.",
    },
    "oyster house": {
        "name": "Chicago Oyster House", "address": "Madison St, the Loop", "lat": 41.8819, "lng": -87.6290,
        "cuisine": "Oyster House", "emoji": "🦪",
        "blurb": "Oysters by rail from the coast, served every way a 1900 kitchen knew.",
        "status": "unknown", "label": "Not yet researched", "today": "The source records no street address, so the pin is a guess in the Loop.",
    },
    # --- added for the NYPL importer -------------------------------------
    "palmer house": {
        "name": "Palmer House", "address": "17 E Monroe St", "lat": 41.8805, "lng": -87.6270,
        "opened": 1871, "closed": None, "cuisine": "Grand Hotel Dining", "emoji": "🏛️",
        "blurb": "Potter Palmer's showpiece hotel, home of the Empire Room.",
        "status": "open", "label": "Still standing", "today": "Palmer House, a Hilton Hotel, on the same site.",
    },
    "empire room": {
        "name": "Empire Room, Palmer House", "address": "17 E Monroe St", "lat": 41.8805, "lng": -87.6270,
        "opened": 1933, "closed": 1976, "cuisine": "Supper Club", "emoji": "🎺",
        "blurb": "The Palmer House's gilded supper club, with a floor show nightly.",
        "status": "open", "label": "Room survives", "today": "The Empire Room is now an event space inside the Palmer House.",
    },
    "henrici": {
        "name": "Henrici's", "address": "67 W Randolph St", "lat": 41.8843, "lng": -87.6302,
        "opened": 1868, "closed": 1962, "cuisine": "Viennese Bakery & Restaurant", "emoji": "🥐",
        "blurb": "The Randolph Street institution of the theater district, famous for coffee and pastry.",
        "status": "gone", "label": "Demolished 1962", "today": "Richard J. Daley Center and its plaza.",
    },
    "fritzel": {
        "name": "Fritzel's", "address": "State St & Lake St", "lat": 41.8857, "lng": -87.6277,
        "opened": 1947, "closed": 1972, "cuisine": "Celebrity Supper Club", "emoji": "🍸",
        "blurb": "State and Lake's see-and-be-seen room, where columnists held court.",
        "status": "gone", "label": "Closed 1972", "today": "Loop retail beside the State/Lake 'L' station.",
    },
    "cape cod room": {
        "name": "Cape Cod Room, The Drake", "address": "140 E Walton Pl", "lat": 41.9003, "lng": -87.6237,
        "opened": 1933, "closed": 2016, "cuisine": "Seafood", "emoji": "🦞",
        "blurb": "The Drake Hotel's nautical seafood room, known for Bookbinder soup.",
        "status": "open", "label": "Hotel still standing", "today": "The Drake is still a hotel; the Cape Cod Room closed in 2016.",
    },
    "drake": {
        "name": "The Drake", "address": "140 E Walton Pl", "lat": 41.9003, "lng": -87.6237,
        "opened": 1920, "closed": None, "cuisine": "Grand Hotel Dining", "emoji": "🏨",
        "blurb": "The lakefront hotel at the top of Michigan Avenue.",
        "status": "open", "label": "Still standing", "today": "The Drake, still a hotel at the same address.",
    },
    "red star inn": {
        "name": "The Red Star Inn", "address": "1528 N Clark St", "lat": 41.9101, "lng": -87.6315,
        "opened": 1899, "closed": 1970, "cuisine": "German", "emoji": "⭐",
        "blurb": "A Bavarian-style inn at Clark and Germania Place, a fixture of the old German North Side.",
        "status": "gone", "label": "Demolished 1970", "today": "Cleared for the Carl Sandburg Village development.",
    },
    "stock yard inn": {
        "name": "Stock Yard Inn", "address": "4178 S Halsted St", "lat": 41.8177, "lng": -87.6462,
        "opened": 1913, "closed": 1976, "cuisine": "Steakhouse", "emoji": "🥩",
        "blurb": "The inn at the Union Stock Yards, where diners in the Sirloin Room branded their own steak.",
        "status": "gone", "label": "Demolished", "today": "The stockyards closed in 1971; the area is now an industrial park.",
    },
    "toffenetti": {
        "name": "Toffenetti Restaurant", "address": "65 W Monroe St", "lat": 41.8807, "lng": -87.6301,
        "cuisine": "Popular-Price Restaurant", "emoji": "🍝",
        "blurb": "Dario Toffenetti's chain of big, busy Loop restaurants with famously florid menu prose.",
        "status": "gone", "label": "Chain closed", "today": "The chain is gone. The pin marks its Monroe Street restaurant.",
    },
    "rector": {
        "name": "Rector's", "address": "Clark St & Monroe St", "lat": 41.8807, "lng": -87.6308,
        "cuisine": "Oyster House", "emoji": "🦪",
        "blurb": "Charles Rector's oyster house, the Loop's fashionable after-theater restaurant.",
        "status": "gone", "label": "Long gone", "today": "Loop office buildings.",
    },
    "chicago athletic": {
        "name": "Chicago Athletic Association", "address": "12 S Michigan Ave", "lat": 41.8817, "lng": -87.6249,
        "opened": 1893, "closed": 2007, "cuisine": "Private Club", "emoji": "🏅",
        "blurb": "A Venetian Gothic clubhouse on Michigan Avenue with a serious members' dining room.",
        "status": "open", "label": "Building survives", "today": "The Chicago Athletic Association hotel, in the restored clubhouse.",
    },
    "university club": {
        "name": "University Club of Chicago", "address": "76 E Monroe St", "lat": 41.8809, "lng": -87.6253,
        "cuisine": "Private Club", "emoji": "🎓",
        "blurb": "A club for college men, founded in 1887.",
        "status": "open", "label": "Club still active", "today": "The club is at 76 E Monroe St, a 1909 building; earlier menus came from a previous clubhouse.",
    },
    "hamilton club": {
        "name": "Hamilton Club of Chicago", "address": "The Loop", "lat": 41.8812, "lng": -87.6296,
        "cuisine": "Private Club", "emoji": "🎩",
        "blurb": "A Republican political and social club with an a la carte dining room.",
        "status": "unknown", "label": "Not yet researched", "today": "Clubhouse location not verified; the pin is a guess in the Loop.",
    },
    "beachcomber": {
        "name": "Don the Beachcomber", "address": "101 E Walton Pl", "lat": 41.9000, "lng": -87.6253,
        "cuisine": "Polynesian / Tiki", "emoji": "🗿",
        "blurb": "The Chicago outpost of the original tiki bar, all rum drinks and Cantonese dishes under thatch.",
        "status": "gone", "label": "Closed", "today": "The Gold Coast block has been redeveloped. Closing date not verified.",
    },
    "fred harvey": {
        "name": "Fred Harvey, Dearborn Station", "address": "Polk St & Dearborn St", "lat": 41.8722, "lng": -87.6292,
        "cuisine": "Railroad Station Restaurant", "emoji": "🚉",
        "blurb": "The Santa Fe's caterer, feeding travellers at the Chicago end of the line.",
        "status": "open", "label": "Station survives", "today": "Dearborn Station still stands, converted to shops and offices.",
    },
}

# Railroads whose dining-car menus are filed under a Chicago name. They are not
# restaurants; they are pinned at the railroad's Chicago terminal.
RAILROADS: dict[str, dict] = {
    "north western": {
        "name": "Chicago & North Western dining car", "address": "North Western Terminal, Madison St & Canal St",
        "lat": 41.8825, "lng": -87.6405,
        "today": "Ogilvie Transportation Center occupies the terminal site.", "status": "gone", "label": "Terminal rebuilt",
    },
    "c. & n. w.": {
        "name": "Chicago & North Western station dining room", "address": "Wells St Station, Wells St & Kinzie St",
        "lat": 41.8887, "lng": -87.6340,
        "today": "The Merchandise Mart stands on the old Wells Street Station site.", "status": "gone", "label": "Demolished",
    },
    "milwaukee & st. paul": {
        "name": "Milwaukee Road dining car", "address": "Union Station, Canal St & Adams St",
        "lat": 41.8787, "lng": -87.6403,
        "today": "Chicago Union Station (the present building opened in 1925).", "status": "open", "label": "Station in use",
    },
    "chicagoan": {
        "name": "Santa Fe 'Chicagoan' dining car (Fred Harvey)", "address": "Dearborn Station, Polk St & Dearborn St",
        "lat": 41.8722, "lng": -87.6292,
        "today": "Dearborn Station still stands, converted to shops and offices.", "status": "open", "label": "Station survives",
    },
    "great western": {
        "name": "Chicago Great Western dining car", "address": "Grand Central Station, Harrison St & Wells St",
        "lat": 41.8743, "lng": -87.6335,
        "today": "Grand Central Station was demolished in 1971.", "status": "gone", "label": "Demolished 1971",
    },
    "alton": {
        "name": "Chicago & Alton buffet car", "address": "Union Depot, Canal St & Adams St",
        "lat": 41.8787, "lng": -87.6403,
        "today": "Chicago Union Station replaced the old Union Depot in 1925.", "status": "gone", "label": "Depot replaced",
    },
    "wisconsin central": {
        "name": "Wisconsin Central station dining room", "address": "Passenger station, Chicago",
        "lat": 41.8743, "lng": -87.6335,
        "today": "Which Chicago station this was is not verified; the pin marks the Grand Central Station site.",
        "status": "unknown", "label": "Not yet researched",
    },
}


def venue_key(name: str) -> str | None:
    """Key of the KNOWN_VENUES entry matching a venue name, if any."""
    name = name.lower().replace("lasalle", "la salle")
    for key in KNOWN_VENUES:
        if key in name:
            return key
    return None


def railroad_key(name: str) -> str | None:
    name = name.lower().replace("-", " ")
    for key in RAILROADS:
        if key in name:
            return key
    return None
