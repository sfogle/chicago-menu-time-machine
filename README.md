# 🕰️ Chicago Menu Time Machine

A delivery app for restaurants you can no longer order from. Spin a random
year, browse the Chicago restaurants that were open, read their menus, check
each dish against the original scan, and see what the bill comes to in 2026
dollars.

```
frontend/                  Vite + React + TypeScript + Tailwind + Leaflet
  public/data/menus.json     restaurants, dishes, prices, bounding boxes
  public/data/cpi_chicago.json   CPI multipliers, 1890-1985 -> 2026 dollars
  public/scans/              menu scan images
pipeline/
  ocr_menu.py                OCR a scan and append it to menus.json
  generate_placeholder_scans.py   rebuild the six seed menus + scans
  build_cpi.py               rebuild cpi_chicago.json
.github/workflows/deploy.yml   build + deploy to GitHub Pages on push to main
```

## Run the app

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173/chicago-menu-time-machine/>. `npm run build`
type-checks and writes the production site to `frontend/dist`.

## Add a real menu scan

### 1. Set up the pipeline (once)

```bash
cd pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
brew install tesseract        # only needed for the Tesseract fallback
```

`requirements.txt` installs PaddleOCR (preferred, a large download; models are
fetched on first run) and pytesseract (fallback). To skip Paddle, comment its
two lines out. Tested with Python 3.10, PaddleOCR 3.7 and Tesseract 5.5.

### 2. OCR a scan

```bash
python ocr_menu.py \
  --image ~/Downloads/berghoff_1952.jpg \
  --restaurant "The Berghoff" --year 1952 --address "17 W Adams St" \
  --lat 41.8793 --lng -87.6285 \
  --opened 1898 \
  --credit "Chicago History Museum" \
  --dry-run
```

`--dry-run` prints the parsed entry and writes nothing. Check the dish table it
prints, then run again without `--dry-run`. That will:

1. copy the image to `frontend/public/scans/<restaurant>-<year>.<ext>`
2. append the entry to `frontend/public/data/menus.json`

Useful flags:

| Flag | Purpose |
| --- | --- |
| `--engine auto\|paddle\|tesseract` | `auto` (default) uses Paddle if installed, else Tesseract |
| `--lat` / `--lng` | Map pin. Without them the pin lands in the middle of the Loop |
| `--geocode` | Look the address up with OpenStreetMap Nominatim instead |
| `--opened` / `--closed` | Years of operation, used to decide which years show the restaurant |
| `--cuisine`, `--blurb`, `--today` | Card text. `--today` is what occupies the address now |
| `--replace` | Overwrite an entry with the same id instead of refusing |

### 3. Review the result

OCR on old menus needs a human pass. Open `menus.json` and fix dish names,
prices and categories, and fill in `stillStanding` (`status` is one of `open`,
`gone`, `moved`, `unknown`). Each dish's `bbox` is `[x, y, width, height]` in
pixels of the scan image; the app scales it, so do not resize the image
without updating `scan.width` / `scan.height` and the boxes.

How the parser decides what is what:

- Text fragments whose vertical centres line up become one row.
- A row ending in a price (`1.65`, `$1.65`, `.45`, `35c`, or a bare number set
  apart by dot leaders) is a dish.
- A short, mostly upper-case row with no price is a category heading.
- An unpriced row directly under a dish becomes its description.
- A bare `45` is read as 45 cents if other prices on the page have decimals, or
  if the menu predates 1960.

Menus with two price columns, prices on the line below the dish, or
handwriting will need manual cleanup.

### Engine accuracy on the seed scans

| Engine | Dishes recovered | Notes |
| --- | --- | --- |
| PaddleOCR | 86 / 86, all prices correct | Slow first run (model download) |
| Tesseract | 9-14 of ~14 per page | Dot leaders confuse it; prices on the typewriter-font page were misread |

Use Paddle when you can.

## About the seed data

- **Menus.** The six seed restaurants are real, as are their addresses and
  rough dates. The dishes and prices are period-plausible reconstructions and
  the scans are generated images, so they are stand-ins, not history. Every
  seed entry has `scan.placeholder: true`. Re-create them with
  `python generate_placeholder_scans.py` (uses macOS system fonts, falls back to
  whatever serif it can find).
- **"Still standing?" notes** are from general knowledge and deserve a check
  before you rely on them, Fritzel's corner especially.
- **Inflation.** `cpi_chicago.json` uses the national BLS CPI-U annual average
  (1982-84 = 100); 1890-1912 are Federal Reserve Bank of Minneapolis estimates.
  The 2026 base (330.0) is an estimate, since the annual average is not
  published until January 2027. To update it, change `BASE_CPI` in
  `pipeline/build_cpi.py` and run it.
- **Sales tax.** `frontend/src/lib/tax.ts` holds combined state + Chicago + RTA
  rates by era (none before 1933). Rates changed mid-year several times, so
  these are approximations.

## Push to GitHub and deploy

```bash
git add -A
git commit -m "Add 1952 Berghoff menu"
git push origin main
```

First time only:

1. Create a GitHub repository named `chicago-menu-time-machine` and add it as
   `origin`. If you use a different name, change `base` in
   `frontend/vite.config.ts` to `/<repo-name>/`.
2. In the repository, go to **Settings → Pages → Build and deployment** and set
   **Source** to **GitHub Actions**.

Every push to `main` then runs `.github/workflows/deploy.yml`, which builds
`frontend/` and publishes `frontend/dist` to
`https://<your-username>.github.io/chicago-menu-time-machine/`.
