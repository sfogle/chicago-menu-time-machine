# 🕰️ Chicago Menu Time Machine

A delivery app for restaurants you can no longer order from. Spin a random
year, browse the Chicago restaurants that were open, read their menus, check
each dish against the original scan, and see what the bill comes to in 2026
dollars.

```
frontend/                     Vite + React + TypeScript + Tailwind + Leaflet
  public/data/menus.json        restaurants, dishes, prices, scan URLs and positions
  public/data/cpi_chicago.json  CPI multipliers, 1890-1985 -> 2026 dollars
pipeline/
  import_nypl_chicago.py        build menus.json from NYPL's transcribed dataset (no OCR)
  import_nypl_scans.py          OCR the few NYPL Chicago scans that were never transcribed
  nypl_api.py                   NYPL Digital Collections API client (needs a free token)
  nypl_colab.ipynb              the same importer, ready to run on Google Colab
  import_cia_chicago.py         add menus from the Culinary Institute of America collection
  clean_menus.py                dish-name cleanup and category rules
  venues.py                     hand-entered facts about known venues
  venue_history.py              sourced building histories and corrections for those venues
  apply_venue_history.py        push venue edits into menus.json without re-importing
  ocr_menu.py                   OCR one scan and add it to menus.json
  fetch_and_ocr_chicago.py      Internet Archive (and Commons) fetch + OCR; --add-missing-ia adds new menus only
  generate_placeholder_scans.py, build_cpi.py
.github/workflows/
  deploy.yml                    build + deploy to GitHub Pages on push to main
  ocr.yml                       manual: OCR a scan URL in the cloud and commit the entry
```

No scan images live in this repository. `menus.json` stores image URLs and the
app loads each scan from its host (NYPL, the Culinary Institute of America or
the Internet Archive) the first time
a visitor opens a dish on that menu.

## Run the app

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173/chicago-menu-time-machine/>. `npm run build`
type-checks and writes the production site to `frontend/dist`.

## Where the menus come from

**35 menus** come from the New York Public Library's
[What's on the Menu?](https://www.nypl.org/research/support/whats-on-the-menu) open dataset: dishes and prices
transcribed by volunteers, so there is no OCR involved. A 36th, Gunther's
1900 "Complete Menu", is an NYPL scan the volunteers never transcribed, read
by OCR: four priced pages in place of the one-page transcription. **62 menus** come from
the [Culinary Institute of America menu collection](https://cdm16940.contentdm.oclc.org/digital/collection/p16940coll1),
transcribed by its library; they run from 1909 to 1983 and cover the two
decades NYPL has nothing for (1930s, 1980s).
**7 more** are Internet Archive hotel menus (1907-1914) read by OCR.

| Decade | Menus | From |
| --- | --- | --- |
| 1890s | 4 | NYPL 4 |
| 1900s | 19 | CIA 1, Internet Archive 2, NYPL 16 |
| 1910s | 7 | CIA 1, Internet Archive 5, NYPL 1 |
| 1920s | 2 | NYPL 2 |
| 1930s | 4 | CIA 4 |
| 1940s | 20 | CIA 15, NYPL 5 |
| 1950s | 12 | CIA 8, NYPL 4 |
| 1960s | 16 | CIA 14, NYPL 2 |
| 1970s | 18 | CIA 16, NYPL 2 |
| 1980s | 3 | CIA 3 |

Things to know about this data:

- **Railroad dining cars are not restaurants.** Ten NYPL entries are dining-car or
  station menus of Chicago railroads, pinned at the line's Chicago terminal and
  labelled as such. They are the dataset's only Chicago material for the 1910s
  and 1920s. Leave them out with `--no-dining-cars`.
- **Later menus have no city in the dataset.** Eleven menus from 1940-1971
  were matched by venue name and then checked against the scan. Seven show a
  Chicago address or the word "Chicago". Four rest on the name and house dishes
  alone: Fritzel's 1950, The Drake 1951, Cape Cod Room 1940 and Stock Yard Inn
  1971. The list and the evidence are in `CONFIRMED_CHICAGO` in the importer.
- **Highlight boxes on NYPL menus are estimates.** The dataset records one
  point per dish (where a volunteer clicked, usually on the first words), not
  a box. The app marks that point and draws a one-line box around it.
- **Venue details are hand-entered, and partly sourced.** 56 of the 77 venues
  have a "Building history" on their card: a few sentences on the building
  and what replaced it, with links to the pages the facts came from
  (`venue_history.py`, checked November 2026). Checking them corrected several
  of the earlier notes. The Sherman House came down in 1980, not 1973. The
  Stock Yard Inn came down in 1977. Gunther's candy building at 214 S State
  still stands. The 1907 "Interstate Hotel Co." menu's address is the
  Lexington Hotel's. Where sources disagree, the history says so or follows
  most of them. The remaining venues' years, pins and notes are from general
  knowledge and should be checked. Chicago renumbered its streets in 1909, so
  pins for older numbered addresses are approximate.
- **CIA menus are placed by matching, and their rights are unreviewed.** The
  CIA transcripts give text but no positions, so the importer OCRs each page
  only to find where each transcribed dish sits; about one dish in ten has no
  highlight. The importer repairs the common transcript slips (spirit-list
  age and strength columns read as dishes, "With cheese" lines that are
  variants of the dish above, headings run into the first dish, garnishes run
  into the name), but busy menus still produce the odd stray line.
  Where a venue has several menus from one year, only the fullest is kept.
  Twelve lesser-known venues have no address on record and share a pin at
  the centre of the Loop. The CIA marks these records "Copyright Not Evaluated", and the
  1980s menus are probably still in copyright, so the app links to the CIA's
  hosted image and never copies it. The 1934 Blue Ribbon Spa date is the
  copyright year printed on the menu; that venue has no address on record and
  is pinned at the centre of the Loop.
- **Categories are assigned by keyword** (`clean_menus.py`), since the dataset
  has none. Expect the odd dish in the wrong section.
- **Some later scans load at a smaller size.** NYPL refuses the 1000px image
  for some menus from 1915 on and serves only its 760px web image; the importer
  detects this and stores that URL instead.

## Rebuild the menus from NYPL

The importer needs only Python 3 and its standard library.

```bash
cd pipeline
python3 import_nypl_chicago.py --dry-run          # show the selection
python3 import_nypl_chicago.py --validate-images  # write menus.json
```

It downloads NYPL's bulk CSV archive (37 MB, cached in the gitignored
`pipeline/nypl_data/`), joins `Menu`, `MenuPage`, `MenuItem` and `Dish`, and
replaces every `nypl-*` entry in `menus.json`. Entries from other sources are
left alone, and an NYPL menu is skipped when another source already has that
venue and year. Useful flags: `--max-menus`, `--per-venue`, `--max-dishes`,
`--no-dining-cars`, `--check-latest` (look on nypl.org for a newer archive).

To run it on Google Colab instead, open `pipeline/nypl_colab.ipynb` there and
run the cells; the last one downloads the finished `menus.json`.

### NYPL scans nobody transcribed

Nearly every Chicago menu NYPL has scanned is already in the transcribed
dataset. Checked against the Digital Collections API in November 2026, only 16
of 1,207 Chicago menu page scans were missing, from three menus. Of those, the
1893 World's Fair clam bake menu is too faint to OCR, and the University Club
menu is a banquet. `import_nypl_scans.py` OCRs the one worth having, Gunther's
1900 (166 dishes on four pages), and replaces the transcribed Gunther's 1900:

```bash
cd pipeline
.venv/bin/python import_nypl_scans.py --dry-run
.venv/bin/python import_nypl_scans.py && python3 clean_menus.py --only ocr
```

It needs no token: the pages come from NYPL's public IIIF server, and the app
loads them from there too. To look for candidates again, `nypl_api.py` uses
the API. Sign up free at https://api.repo.nypl.org/sign_up, then put the
emailed token in `pipeline/.nypl_token` (gitignored) or the `NYPL_API_TOKEN`
environment variable. `python3 nypl_api.py --check` tests it without printing it.

Being polite to NYPL: images are requested at 1000px wide, never full size;
`--validate-images` sends HEAD requests only, two a second, and caches the
answers; the app never preloads scans and fetches each page image once.

## Add menus from the Culinary Institute of America

```bash
cd pipeline
python3 import_cia_chicago.py --dry-run             # show what would be imported
python3 import_cia_chicago.py                       # 1930s and 1980s (the default)
python3 import_cia_chicago.py --decades 1900s 1910s 1930s 1940s 1950s 1960s 1970s 1980s   # everything
```

It asks the CIA's CONTENTdm server for records whose city is Chicago in each
decade, reads every page's transcript and turns priced lines into dishes,
keeping the menu's own section headings. Standard library only. If the
`tesseract` program is installed it also places a highlight box for each dish;
`--no-locate` skips that. It replaces the `cia-*` entries for the decades you
name and leaves everything else alone.

Being polite to the CIA: one request a second, every answer cached in the
gitignored `pipeline/cia_data/`, and images requested at most 1600px on the
long side (double-page spreads are unreadable below that).

## Add or correct a venue's history

Venue facts live in `pipeline/venues.py`, and sourced histories in
`pipeline/venue_history.py`. Each history is a few sentences plus a list of
`(label, url)` sources, and can override the venue's label, status, "today"
note or pin. The importers copy these into each menu as they build it. To
push an edit into the menus already in `menus.json`, run:

```bash
cd pipeline
python3 apply_venue_history.py --dry-run   # list the menus that would change
python3 apply_venue_history.py
```

It never touches menu names or dishes. It fills in cuisine, emoji and blurb
only where an entry still has the importer's placeholder.

## Add new Internet Archive menus

```bash
cd pipeline
.venv/bin/python fetch_and_ocr_chicago.py --add-missing-ia --engine paddle --dry-run
.venv/bin/python fetch_and_ocr_chicago.py --add-missing-ia --engine paddle --no-geocode
python3 clean_menus.py --only ocr
python3 apply_venue_history.py
```

This lists every dated, licensed Chicago menu on the Internet Archive with a
named venue. It skips venue-years `menus.json` already has, OCRs every page,
and appends the page with the most priced dishes. Existing entries are left
alone, and the app loads the page image from archive.org. Most of the
Lexington Hotel's holiday menus (1900, 1904, 1909) are fixed-price dinners
with no prices, so they are skipped. The November 2026 run added the
Lexington Hotel 1908 and the Congress Hotel 1914. OCR sometimes runs two
dishes on one line into a single name ("Easter Eggs en Nest 40 Frozen Egg
Nog").

## Add a menu that nobody has transcribed

### In the cloud (no local setup)

On GitHub: **Actions → OCR a menu scan → Run workflow**, then fill in the
image URL, restaurant, year, address, cuisine and credit. The runner downloads
the scan, OCRs it with Tesseract, commits the entry to `menus.json` and starts
a deploy. The image is not copied into the repo, so its URL must stay public.

Tesseract is the weaker engine: expect to hand-correct names and prices in
`menus.json` afterwards.

### On your machine

```bash
cd pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```bash
python ocr_menu.py \
  --image ~/Downloads/berghoff_1952.jpg \
  --restaurant "The Berghoff" --year 1952 --address "17 W Adams St" \
  --lat 41.8793 --lng -87.6285 --opened 1898 \
  --credit "Chicago History Museum" \
  --dry-run
```

`--dry-run` prints the parsed entry and writes nothing. Without it the entry
is added to `menus.json`. Pass `--scan-url https://…` to have the app load the
image from that URL; otherwise the file is copied into
`frontend/public/scans/`. Other flags: `--engine auto|paddle|tesseract`,
`--geocode`, `--opened` / `--closed`, `--cuisine`, `--blurb`, `--today`,
`--replace`. Run `python clean_menus.py --only ocr` afterwards to tidy names
and assign categories.

`requirements.txt` installs PaddleOCR (accurate, large) and pytesseract (needs
`brew install tesseract`). On the six generated test scans PaddleOCR recovers
86 of 86 dishes; Tesseract gets 9-14 of about 14 per page.

How the OCR parser decides what is what:

- Text fragments whose vertical centres line up become one row, and a row is
  split into cells at each price, so multi-column menus give one dish per column.
- A cell ending in a price (`1.65`, `$1.65`, `.45`, `35c`, or a bare multiple
  of five such as `25`) is a dish. A bare number is read as cents if other
  prices on the page have decimals or the menu predates 1960.
- A short, mostly upper-case row with no price is a section heading.
- An unpriced row directly under a single-column dish is its description.

## menus.json in brief

Each restaurant has `scan` (first page: `src`, optional `fallbackSrc`,
`width`, `height`, credit and source link) and, for multi-page menus,
`pages`. Each dish has a `price` in the menu year's dollars and one of:

- `bbox`: `[x, y, width, height]` in pixels of the page image (OCR'd menus)
- `pos`: `[x, y]` as fractions of the page, 0 to 1 (NYPL menus), with `page`
  giving the index into `pages`

`src` may be a full `https://` URL or a path under `frontend/public/`.

## Inflation and tax

- `cpi_chicago.json` uses the national BLS CPI-U annual average
  (1982-84 = 100); 1890-1912 are Federal Reserve Bank of Minneapolis estimates.
  The 2026 base (330.0) is an estimate until BLS publishes the annual average
  in January 2027. To update it, change `BASE_CPI` in `pipeline/build_cpi.py`
  and run it.
- `frontend/src/lib/tax.ts` holds combined state + Chicago + RTA sales tax
  rates by era (none before 1933). Rates changed mid-year several times, so
  these are approximations.

## Push to GitHub and deploy

```bash
git add -A
git commit -m "Add 1952 Berghoff menu"
git push origin main
```

Every push to `main` runs `.github/workflows/deploy.yml`, which builds
`frontend/` and publishes `frontend/dist` to
`https://<your-username>.github.io/chicago-menu-time-machine/`. First-time
setup: **Settings → Pages → Source: GitHub Actions**. If the repository has a
different name, change `base` in `frontend/vite.config.ts` to `/<repo-name>/`.
