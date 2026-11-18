"""Sourced building histories for the venues in venues.py.

Each entry adds to (and where noted corrects) the matching KNOWN_VENUES or
RAILROADS entry: a short history of the building, what stands there now, and
the pages the facts came from. Everything here was checked against the linked
sources in November 2026. Where sources disagreed, the text says so or uses
the date most of them give. Keep claims to what a linked page supports.

`sources` is a list of (label, url) pairs, best source first.
"""
from __future__ import annotations

WIKI = "https://en.wikipedia.org/wiki/"

# Venues the importers matched by name but venues.py did not know about.
NEW_VENUES: dict[str, dict] = {
    "hoe sai gai": {
        # Nominatim put this half a mile west; 75-85 W Randolph is on the Daley Center block.
        "name": "Hoe Sai Gai", "address": "75-85 W Randolph St", "lat": 41.8843, "lng": -87.6306,
        "opened": 1932, "closed": 1962, "cuisine": "Chinese & American", "emoji": "🥢",
        "blurb": "A big Art Deco Chinese restaurant on Randolph Street, chop suey on one side of the menu and steaks on the other.",
        "status": "gone", "label": "Demolished 1962", "today": "Richard J. Daley Center and its plaza.",
    },
    "sayat nova": {
        "name": "Sayat Nova", "address": "157 E Ohio St", "lat": 41.89234, "lng": -87.62323,
        "opened": 1970, "closed": None, "cuisine": "Armenian", "emoji": "🫓",
        "blurb": "Armenian and Middle Eastern cooking a block off Michigan Avenue, named for an 18th-century Armenian poet.",
        "status": "open", "label": "Still open", "today": "Sayat Nova, at the same address.",
    },
    "maxim's": {
        "name": "Maxim's de Paris", "address": "1300 N Astor St", "lat": 41.906, "lng": -87.62763,
        "opened": 1963, "closed": 1982, "cuisine": "French", "emoji": "🥂",
        "blurb": "An Art Nouveau copy of the Paris original, in the basement of Bertrand Goldberg's Astor Tower.",
        "status": "open", "label": "Room survives", "today": "The restored dining room reopened in 2022 as The Astor Club.",
    },
    "gritzbe": {
        "name": "Great Gritzbe's Flying Food Show", "address": "21 E Chestnut St", "lat": 41.89814, "lng": -87.6272,
        "opened": 1974, "closed": 1983, "cuisine": "American", "emoji": "🎪",
        "blurb": "An early Rich Melman restaurant with a cheese bar, a dessert bar and a deliberately silly name.",
        "status": "gone", "label": "Closed 1983", "today": "A condominium building occupies the site.",
    },
    "standard india": {
        "name": "Standard India Restaurant", "address": "2546 W Devon Ave", "lat": 41.99785, "lng": -87.69421,
        "closed": 2013, "cuisine": "Indian", "emoji": "🍛",
        "blurb": "Said to be the first Indian restaurant on Devon Avenue, as the street became Chicago's Little India.",
        "status": "gone", "label": "Closed", "today": "It moved to 917 W Belmont Ave and closed there around 2013.",
    },
    "sweetwater": {
        "name": "Sweetwater", "address": "1028 N Rush St", "lat": 41.90136, "lng": -87.62808,
        "cuisine": "American", "emoji": "🍸",
        "blurb": "A Rush Street restaurant opened in 1976 in the old Mister Kelly's nightclub space.",
        "status": "unknown", "label": "Not verified", "today": "Sources disagree on what now stands on the corner of Rush and Bellevue.",
    },
    "water tower inn": {
        "name": "Coach and Four, Water Tower Inn", "address": "800 N Michigan Ave", "lat": 41.8978, "lng": -87.6244,
        "cuisine": "Hotel Dining Room", "emoji": "🐎",
        "blurb": "A dining room in the Water Tower Inn, a 1960s motor hotel on Michigan Avenue.",
        "status": "gone", "label": "Demolished", "today": "Park Tower (2000), home of the Park Hyatt Chicago.",
    },
    # The 1907 Internet Archive menu gives this company name and 2135 S Michigan Ave,
    # which is the Lexington Hotel's address.
    "interstate hotel": {
        "name": "Interstate Hotel Co.", "address": "2135 S Michigan Ave", "lat": 41.8530, "lng": -87.6238,
        "opened": 1892, "closed": 1980, "cuisine": "Hotel Dining Room", "emoji": "🏨",
        "blurb": "The menu's address, 2135 S Michigan Ave, is the Lexington Hotel's.",
        "status": "gone", "label": "Demolished 1995", "today": "The Lex, an apartment tower completed in 2012.",
    },
}

_LEXINGTON = {
    "history": "Built at 2135 S Michigan for visitors to the 1893 World's Fair. Al Capone ran his operation "
               "from the hotel from 1928 until his arrest in 1931. It was demolished in 1995 despite its landmark listings.",
    "today": "The Lex, a 296-unit apartment tower completed in 2012.",
    "sources": [("Wikipedia: Lexington Hotel", WIKI + "Lexington_Hotel_(Chicago)")],
}

_DEARBORN = {
    "history": "Dearborn Station was the Santa Fe's Chicago terminal, and Fred Harvey fed its passengers. "
               "The last intercity train left on April 30, 1971. The train shed came down in 1976, and the "
               "headhouse became shops and offices in the 1980s.",
    "sources": [("Wikipedia: Dearborn Station", WIKI + "Dearborn_Station"),
                ("Chicago History Museum: Meals by Fred Harvey", "https://www.chicagohistory.org/meals-by-fred-harvey/")],
}

_UNION_STATION = {
    "history": "The first Union Depot opened at Canal and Adams in 1881. It was demolished in 1924, and the present "
               "Union Station opened in 1925.",
    "sources": [("Encyclopedia of Chicago: Union Station", "https://encyclopedia.chicagohistory.org/pages/1739.html"),
                ("Wikipedia: Chicago Union Station", WIKI + "Chicago_Union_Station")],
}

_GRAND_CENTRAL = {
    "history": "Solon S. Beman designed Grand Central Station, which a Wisconsin Central company began building in "
               "1889. It opened on December 8, 1890, with a restaurant and, until 1901, a hotel. The B&O bought it in 1910. "
               "It closed in 1969 and was demolished in 1971, and the lot stayed empty for nearly 50 years.",
    "sources": [("Wikipedia: Grand Central Station (Chicago)", WIKI + "Grand_Central_Station_(Chicago)"),
                ("Preservation Chicago: Grand Central Station",
                 "https://www.preservationchicago.org/grand-central-station-chicago-by-solon-s-beman-built-1890-demolished-1971-photos-by-richard-nickel-art-institute-of-chicago-archival-image-collection/")],
}

HISTORY: dict[str, dict] = {
    "blackstone": {
        "history": "Marshall & Fox built it in 1908–10 on the site of railroad president Timothy Blackstone's mansion. "
                   "It became a Chicago Landmark in 1998 and reopened in 2008 after a long decline and a full restoration.",
        "sources": [("Wikipedia: Blackstone Hotel", WIKI + "Blackstone_Hotel"),
                    ("Open House Chicago: The Blackstone", "https://openhousechicago.org/sites/site/the-blackstone-hotel/")],
    },
    "congress": {
        "history": "It opened in 1893 as the Auditorium Annex, joined to the Auditorium across Congress Street by an "
                   "underground marble passage called Peacock Alley. Holabird & Roche added a south tower in the 1900s, "
                   "and the hotel took the Congress name in 1911.",
        "sources": [("Wikipedia: Congress Plaza Hotel", WIKI + "Congress_Plaza_Hotel"),
                    ("Congress Plaza Hotel: History", "https://www.congressplazahotel.com/history")],
    },
    "la salle": {
        "history": "Holabird & Roche designed it, and it opened in 1909. A fire in June 1946 killed 61 people. The hotel "
                   "was rebuilt and reopened in 1947, then closed and was demolished in 1976.",
        "today": "2 North LaSalle, an office tower completed in 1979.",
        "sources": [("Wikipedia: La Salle Hotel", WIKI + "La_Salle_Hotel"),
                    ("Chicagoist: The LaSalle Hotel fire", "https://chicagoist.com/2012/06/05/one_for_the_road_38.php")],
    },
    "lexington": dict(_LEXINGTON),
    "interstate hotel": dict(_LEXINGTON),
    "sherman house": {
        "label": "Demolished 1980",
        "history": "This was the fourth Sherman House on the corner, built by Holabird & Roche in 1911 with a 1920s annex, "
                   "and home of the College Inn. The hotel closed in 1973 and was demolished in 1980.",
        "today": "The James R. Thompson Center (1985) fills the block.",
        "sources": [("Wikipedia: Sherman House Hotel", WIKI + "Sherman_House_Hotel"),
                    ("Preservation Chicago: Sherman House", "https://www.preservationchicago.org/?p=10293")],
    },
    "chicago beach": {
        "label": "Demolished 1970",
        "history": "Warren Leland built it in 1892 for World's Fair visitors. The original building came down in 1927 "
                   "while a newer wing carried on. After World War II the Army used it as a headquarters until 1967, "
                   "and it was demolished in 1970.",
        "today": "The Regents Park apartment towers.",
        "sources": [("Wikipedia: Chicago Beach Hotel", WIKI + "Chicago_Beach_Hotel"),
                    ("Clio: Chicago Beach Hotel, 1892–1970", "https://theclio.com/entry/11217")],
    },
    "gunther": {
        "address": "214 S State St", "lat": 41.8789, "lng": -87.6276,
        "status": "open", "label": "Building survives",
        "history": "Candymaker Charles F. Gunther lost his Clark Street shop in the 1871 fire. He built a factory and "
                   "salesroom at 212 State Street, completed in 1887, with his famous museum of curiosities on site. "
                   "Under the 1911 renumbering the address became 214 S State St.",
        "today": "The building still stands, empty and owned by the federal government. A 2024 decision spared it from demolition.",
        "sources": [("Wikipedia: 214 South State Street", WIKI + "214_South_State_Street"),
                    ("WTTW: The Chicagoan credited with popularizing caramels", "https://interactive.wttw.com/node/32051"),
                    ("The Real Deal: Federal government opts against demolition",
                     "https://therealdeal.com/chicago/2024/08/05/federal-government-opts-against-demo-for-two-chicago-buildings")],
    },
    "brauer": {
        "history": "Brothers Paul and Caspar Brauer, German immigrants, ran this State Street cafe, one of the city's "
                   "leading restaurants in the 1890s. In the 1900s they took over Lincoln Park's concessions and its "
                   "new Prairie School refectory, which still carries the Café Brauer name.",
        "sources": [("Wikipedia: Café Brauer", WIKI + "Caf%C3%A9_Brauer")],
    },
    "rector": {
        "history": "Charles Rector, once a cashier at the Boston Oyster House, opened his oyster house at Clark and "
                   "Monroe in 1884. It was an immediate success, and he went on to open Rector's on Broadway in New York.",
        "sources": [("Daytonian in Manhattan: The lost Rector's restaurant",
                     "https://daytoninmanhattan.blogspot.com/2023/01/the-lost-rectors-restaurant-1508-1510.html")],
    },
    "palmer house": {
        "history": "Today's building is the third Palmer House, built in 1923–25 by Holabird & Roche on the site of "
                   "the 1875 hotel, so menus from before 1925 come from the older building. Conrad Hilton bought it in "
                   "1945, and it became a Chicago Landmark in 2006.",
        "sources": [("Wikipedia: The Palmer House Hilton", WIKI + "The_Palmer_House_Hilton"),
                    ("City of Chicago landmark report",
                     "https://www.chicago.gov/dam/city/depts/zlup/Historic_Preservation/Publications/Palmer_House_Hotel.pdf")],
    },
    "henrici": {
        "history": "Founded in 1868, the restaurant later occupied an 1895 building by Holsman & Hunt at 67–71 W Randolph. "
                   "It closed in August 1962, when the whole block was cleared for the Civic Center.",
        "sources": [("WTTW: What happened to Chicago's most famous restaurant?",
                     "https://news.wttw.com/2018/04/25/ask-geoffrey-what-happened-chicago-s-most-famous-restaurant"),
                    ("Art Institute, Ryerson & Burnham: Henrici's", "https://archive.artic.edu/ryerson/2004"),
                    ("Encyclopedia of Chicago", "https://encyclopedia.chicagohistory.org/pages/11590.html")],
    },
    "fritzel": {
        "address": "201 N State St",
        "history": "Mike Fritzel and Joe Jacobson opened it at 201 N State in 1947. Trade fell away in the late 1960s, "
                   "after the McCormick Place fire cut convention business, and it closed in 1972.",
        "sources": [("Chicago History Museum: Fritzel's", "https://www.chicagohistory.org/chicago-finest-eating-house/")],
    },
    "cape cod room": {
        "history": "The Drake's seafood room opened in 1933. Marilyn Monroe and Joe DiMaggio are said to have carved "
                   "their initials into its bar.",
        "sources": [("Wikipedia: Drake Hotel", WIKI + "Drake_Hotel_(Chicago)"),
                    ("The Drake: History", "https://www.thedrakehotel.com/history/")],
    },
    "drake": {
        "history": "Marshall & Fox designed it for the Drake brothers, and it opened on New Year's Eve 1920. "
                   "Hilton bought it in 2006.",
        "sources": [("Wikipedia: Drake Hotel", WIKI + "Drake_Hotel_(Chicago)"),
                    ("The Drake: History", "https://www.thedrakehotel.com/history/")],
    },
    "red star inn": {
        "label": "Gone",
        "history": "Carl Gallauer, an immigrant from Cologne, opened Zum Roten Stern on October 7, 1899, and bought "
                   "the building in 1922. It once had a Clark Street address further south; this pin is the 1528 N Clark location.",
        "today": "Said to have been cleared for the Carl Sandburg Village area; the demolition date is not verified.",
        "sources": [("Chicago Ancestors: Red Star Inn", "https://www.chicagoancestors.org/node/49271"),
                    ("Chicago Ancestors: The Red Star Inn, 1528 N Clark", "https://chicagoancestors.org/node/50996")],
    },
    "stock yard inn": {
        "label": "Demolished 1977",
        "history": "It was built in 1912–13 to replace the Transit House hotel after a fire. When the stockyards closed "
                   "in 1971 the inn went with them, and it was torn down in January 1977.",
        "today": "The site at Halsted and Exchange is a vacant lot.",
        "sources": [("Art Institute, Ryerson & Burnham: Stock Yard Inn", "https://archive.artic.edu/ryerson/2043"),
                    ("Chicago History Museum: demolition photo, 1977", "https://images.chicagohistory.org/asset/340175")],
    },
    "toffenetti": {
        "history": "Dario Toffenetti had six Loop restaurants under the Toffenetti-Triangle name by 1937. After his "
                   "death in 1962 his family ran them until about 1980.",
        "sources": [("Restaurant-ing Through History: Dario Toffenetti",
                     "https://restaurant-ingthroughhistory.com/2009/10/26/anatomy-of-a-restaurateur-dario-toffenetti/")],
    },
    "chicago athletic": {
        "history": "Henry Ives Cobb's Venetian Gothic clubhouse opened in 1893, the World's Fair year. It became a "
                   "Chicago Landmark in 1996, stood empty after the club closed in 2007, and reopened as a hotel in 2015.",
        "sources": [("Open House Chicago: Chicago Athletic Association",
                     "https://openhousechicago.org/sites/site/chicago-athletic-association-hotel/"),
                    ("Chicago Architecture Center: Restoring the CAA",
                     "https://www.architecture.org/online-resources/stories-of-chicago/restoring-the-chicago-athletic-association")],
    },
    "university club": {
        "history": "The club was chartered in 1887. Holabird & Roche built its Gothic clubhouse at Michigan and Monroe "
                   "in 1907–09, and William Holabird was one of the club's founding members.",
        "sources": [("Wikipedia: University Club of Chicago", WIKI + "University_Club_of_Chicago"),
                    ("University Club: History", "https://www.ucco.com/the-club/history")],
    },
    "hamilton club": {
        "history": "It was organized in 1890 to promote Republican principles. A 1919 plan shows a clubhouse at "
                   "14–26 S Dearborn St.",
        "today": "Where the club met in 1900 is not verified, so the pin is a guess in the Loop.",
        "sources": [("SNAC: Hamilton Club of Chicago", "https://snaccooperative.org/view/58838492"),
                    ("Chicago History Museum: 1919 clubhouse plan", "https://images.chicagohistory.org/asset/153879/")],
    },
    "beachcomber": {
        "label": "Closed 1981",
        "history": "It opened on May 1, 1940, as the Chicago branch of Hollywood's original tiki bar. Tribune archives "
                   "list it at 101 E Walton until 1981.",
        "today": "The Gold Coast block has since been redeveloped.",
        "sources": [("Chicago Tribune via AOL: Vintage tiki bars",
                     "https://www.aol.com/articles/vintage-chicago-tribune-tiki-bars-202500692.html"),
                    ("mytiki.life: Don the Beachcomber, Chicago", "https://mytiki.life/tiki-bars/don-the-beachcomber-1")],
    },
    "union station": {
        "history": "The present Union Station opened in 1925. Fred Harvey ran its lunch room and coffee shop until a "
                   "1980 fire destroyed that part of the station. The Clinton Street entrance reopened through the old "
                   "restaurant space in 2023.",
        "sources": [("Chicago History Museum: Meals by Fred Harvey", "https://www.chicagohistory.org/meals-by-fred-harvey/"),
                    ("Preservation Chicago: Clinton Street entrance reopens",
                     "https://www.preservationchicago.org/win-after-40-years-union-stations-clinton-street-entrance-reopens-through-former-fred-harvey-restaurant-space-chicago-7-2018/")],
    },
    "marshall field": {
        "history": "The Walnut Room opened in 1907 as the South Grill Room and is often called the oldest "
                   "department-store restaurant in the country. Macy's bought Field's in 2005 and renamed the store in 2006.",
        "sources": [("Tasting Table: History of the Walnut Room", "https://tastingtable.com/1649474/the-walnut-room-history-chicago"),
                    ("Wikipedia: Marshall Field and Company Building", WIKI + "Marshall_Field_and_Company_Building")],
    },
    "kungsholm": {
        "history": "The restaurant moved into the 1895 McCormick mansion at Rush and Ontario in 1937 and added a "
                   "miniature puppet opera around 1940. Both closed in 1971. Lawry's The Prime Rib followed, from 1974 to 2020.",
        "today": "The mansion is now The Hand & The Eye.",
        "sources": [("Chicago History Museum: Kungsholm Miniature Opera", "https://www.chicagohistory.org/?p=6147"),
                    ("Preservation Chicago: The McCormick Mansion's reuse",
                     "https://www.preservationchicago.org/win-the-hand-the-eyes-remarkable-and-extraordinary-reuse-of-the-mccormick-mansion/")],
    },
    "auditorium hotel": {
        "history": "Adler & Sullivan's 1889 Auditorium Building combined a theater, offices and this hotel. The city ran "
                   "it as a servicemen's center during World War II, and Roosevelt University took it over in 1946 and "
                   "turned the hotel rooms into classrooms.",
        "sources": [("Wikipedia: Auditorium Building", WIKI + "Auditorium_Building")],
    },
    "morrison hotel": {
        "label": "Demolished 1965",
        "history": "It was razed in 1965 to clear the site for the First National Bank tower. At the time it was said "
                   "to be the tallest building ever demolished.",
        "today": "Chase Tower (1969), 10 S Dearborn St.",
        "sources": [("Wikipedia: Morrison Hotel", WIKI + "Morrison_Hotel_(Chicago)"),
                    ("Chicago YIMBY: Lost Legends, the Morrison Hotel",
                     "https://chicagoyimby.com/2023/03/lost-legends-2-the-morrison-hotel-in-the-loop.html")],
    },
    "stevens hotel": {
        "history": "It opened on May 2, 1927, as the largest hotel in the world, with 3,000 rooms. Conrad Hilton bought "
                   "it in 1945.",
        "sources": [("Historic Hotels of America: Hilton Chicago",
                     "https://www.historichotels.org/us/hotels-resorts/hilton-chicago/history.php")],
    },
    "blackhawk": {
        "label": "Closed 1984",
        "history": "Otto Roth opened it on December 27, 1920, in a post-fire building by John M. Van Osdel. His son "
                   "Don Roth closed it on August 31, 1984.",
        "today": "The restaurant closed in 1984. What became of the building is not verified.",
        "sources": [("Wikipedia: Blackhawk (restaurant)", WIKI + "Blackhawk_(restaurant)"),
                    ("UIC Today: Legendary restaurant remembered",
                     "https://today.uic.edu/legendary-chicago-restaurant-remembered-in-uic-archives")],
    },
    "trianon": {
        "label": "Demolished 1967",
        "history": "It opened in 1922 at 62nd and Cottage Grove in Woodlawn and was demolished in 1967 to make room "
                   "for low-income housing.",
        "today": "Housing built after the ballroom came down in 1967.",
        "sources": [("Chicago History Museum: Trianon Ballroom", "https://www.chicagohistory.org/trianon-ballroom/"),
                    ("Wikipedia: Trianon Ballrooms", WIKI + "Trianon_Ballrooms")],
    },
    "wrigley building": {
        "history": "William Wrigley Jr.'s company kept its headquarters in the building until 2012. Lou Malnati's "
                   "opened in the north tower in 2019.",
        "sources": [("Wikipedia: Wrigley Building", WIKI + "Wrigley_Building"),
                    ("ABC7: Lou Malnati's opens in the Wrigley Building",
                     "https://abc7chicago.com/post/new-lou-malnatis-opens-on-magnificent-mile/5621063/")],
    },
    "edgewater beach": {
        "label": "Demolished 1971",
        "history": "Marshall & Fox designed it; it opened in 1916, and a tower followed in 1923. Landfill for Lake Shore "
                   "Drive cut it off from the lake in the 1950s. It closed in December 1967 and was demolished by 1971.",
        "today": "Only the pink Edgewater Beach Apartments (1928), up the street at 5555 N Sheridan, survive.",
        "sources": [("Wikipedia: Edgewater Beach Hotel", WIKI + "Edgewater_Beach_Hotel"),
                    ("Preservation Chicago: Edgewater Beach Hotel",
                     "https://www.preservationchicago.org/edgewater-beach-hotel-by-marshall-fox-built-1916-1923-demolished-1971/")],
    },
    "pump room": {
        "history": "Hotelier Ernie Byfield opened the Pump Room in the Ambassador East on October 1, 1938. Booth One "
                   "was kept for stars, from Gertrude Lawrence to Humphrey Bogart and Lauren Bacall.",
        "sources": [("Classic Chicago: The Glamorous Thirties", "https://classicchicagomagazine.com/?p=31668"),
                    ("Wikipedia: Ernie Byfield", WIKI + "Ernie_Byfield")],
    },
    "cafe bohemia": {
        "opened": 1936, "closed": 1986, "status": "gone", "label": "Closed 1986",
        "history": "Joe Basek, a hunter, opened it in 1936 and served game: bear, lion, moose, and the buffalo burger "
                   "the restaurant claimed to have invented. It closed in 1986, and the building was sold to developers.",
        "today": "What stands at 138 S Clinton today is not verified.",
        "sources": [("Chicagoist: Restaurant flashback, Cafe Bohemia",
                     "https://chicagoist.com/2012/02/15/restaurant_flashback_cafe_bohemia_s.php"),
                    ("Digital Research Library of Illinois History: Cafe Bohemia",
                     "https://drloihjournal.blogspot.com/2021/08/eating-lion-tiger-and-bear-at-cafe-bohemia-chicago.html")],
    },
    "london house": {
        "history": "The jazz room in the 1923 London Guarantee Building ran until January 1975, with Ramsey Lewis as "
                   "its last headliner. The building reopened as the LondonHouse hotel in 2016.",
        "sources": [("Wikipedia: London House (Chicago)", WIKI + "London_House_(Chicago)")],
    },
    "berghoff": {
        "history": "Herman Berghoff opened on Adams Street in 1898. The storefronts at 17 W Adams date from 1872 and "
                   "were among the first rebuilt after the Great Fire.",
        "sources": [("The Berghoff: History", "https://www.theberghoff.com/history/"),
                    ("Open House Chicago: Berghoff Restaurant", "https://openhousechicago.org/sites/site/berghoff-restaurant")],
    },
    "fred harvey": dict(_DEARBORN),
    "brown's": {
        "history": "The ground floor at 226 S Wabash was the 226 Club in the 1920s and the Wonder Bar in the 1930s and "
                   "'40s. Brown's ran here from the 1950s until early 1969.",
        "sources": [("Exchequer Restaurant & Pub: History", "https://www.exchequerpub.com/history")],
    },
    "hoe sai gai": {
        "history": "Joe Eng had run a jazz-age cafe in Garfield Park. In 1932 he opened Hoe Sai Gai on Randolph Street, "
                   "with Art Deco dining rooms popular with theatergoers. It was demolished in 1962 for the Civic Center, "
                   "on the same block as Henrici's.",
        "sources": [("Axios Chicago: This 1920s Chinese cafe served up Chicago jazz",
                     "https://www.axios.com/local/chicago/2026/04/28/this-1920s-chinese-cafe-served-up-chicago-jazz"),
                    ("DocStudio: Western culture meets Eastern culture in Hoe Sai Gai",
                     "https://docstudio.org/2021/12/16/western-culture-meets-eastern-culture/")],
    },
    "sayat nova": {
        "history": "It has served Armenian food at 157 E Ohio since about 1970.",
        "sources": [("WTTW Check, Please!: Sayat Nova", "https://checkplease.wttw.com/content/sayat-nova"),
                    ("Time Out Chicago: Sayat Nova", "https://www.timeout.com/chicago/restaurants/sayat-nova")],
    },
    "maxim's": {
        "history": "Nancy Goldberg opened it in December 1963 in the basement of Astor Tower, designed by her husband, "
                   "Bertrand Goldberg, and ran it until the early 1980s. Their heirs gave it to the city in 2000.",
        "sources": [("Bertrand Goldberg Archive: Maxim's", "https://bertrandgoldberg.org/works/maxims"),
                    ("Preservation Chicago: Maxim's to reopen as the Astor Club",
                     "https://www.preservationchicago.org/win-maxims-to-reopen-as-the-astor-club-in-late-2022/")],
    },
    "gritzbe": {
        "history": "Rich Melman's Lettuce Entertain You opened it in 1974. Business slowed, the name became "
                   "\"Not So Great Gritzbe's\" in 1982, and it closed in 1983.",
        "sources": [("Wikipedia: The Great Gritzbe's Flying Food Show", WIKI + "The_Great_Gritzbe%27s_Flying_Food_Show"),
                    ("UPI, 1982: Restaurant owns up to its non-greatness",
                     "https://www.upi.com/Archives/1982/05/05/Restaurant-owns-up-to-its-non-greatness/6679389419200/")],
    },
    "standard india": {
        "history": "Devon Avenue's first Indian store opened in 1972. Standard India is described as the first Indian "
                   "restaurant on the street; its opening year is not verified.",
        "sources": [("WTTW Check, Please!: Standard India (closed)",
                     "https://checkplease.wttw.com/content/standard-india-restaurant-closed"),
                    ("WBEZ: How Devon Avenue became Chicago's Little India",
                     "https://www.wbez.org/curious-city/2022/11/17/how-did-devon-avenue-become-chicagos-little-india")],
    },
    "sweetwater": {
        "history": "A Chicago Tribune review in July 1976 describes the new restaurant in the former Mister Kelly's, "
                   "the nightclub that ran here from 1953 to 1975.",
        "sources": [("Wikipedia: Mister Kelly's", WIKI + "Mr._Kelly%27s"),
                    ("Chicago Tribune, July 23, 1976 (Newspapers.com)", "https://www.newspapers.com/newspage/383805698")],
    },
    "water tower inn": {
        "history": "The Water Tower Inn dates from about 1962 and later became the Park Hyatt. It was demolished, and "
                   "Park Tower, completed in 2000, now stands at 800 N Michigan.",
        "sources": [("UIC Digital Collections: Water Tower Inn", "https://digital.library.uic.edu/view/ark:/81984/d3tq27"),
                    ("Skyscraper Center: Park Tower", "https://www.skyscrapercenter.com/building/park-tower/793")],
    },
}

RAILROAD_HISTORY: dict[str, dict] = {
    "north western": {
        "history": "The C&NW opened this terminal at Madison and Canal in 1911; menus from before then come from the "
                   "Wells Street Station. The headhouse was demolished in 1984 for the Citicorp Center (1987), now the "
                   "Ogilvie Transportation Center, where Metra trains still run.",
        "sources": [("Wikipedia: Ogilvie Transportation Center", WIKI + "Ogilvie_Transportation_Center")],
    },
    "c. & n. w.": {
        "history": "The C&NW's Wells Street Station opened in 1881 at Wells and Kinzie. It was replaced for passengers "
                   "in 1911 by the Madison Street terminal, and the Merchandise Mart (1930) was built over the site.",
        "sources": [("Wikipedia: Wells Street Station", WIKI + "Wells_Street_Station")],
    },
    "milwaukee & st. paul": dict(_UNION_STATION),
    "alton": dict(_UNION_STATION),
    "chicagoan": dict(_DEARBORN),
    "great western": dict(_GRAND_CENTRAL),
    "wisconsin central": {
        **_GRAND_CENTRAL,
        "address": "Grand Central Station, Harrison St & Wells St",
        "status": "gone", "label": "Demolished 1971",
        "today": "Grand Central Station was demolished in 1971.",
    },
}
