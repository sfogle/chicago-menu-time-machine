export type BBox = [x: number, y: number, w: number, h: number]

export interface Dish {
  id: string
  name: string
  description: string
  category: string
  price: number
  /** Pixel box on the scan image: [x, y, width, height]. Present for OCR'd menus. */
  bbox?: BBox
  /**
   * Normalised (0-1) point on the page, [x, y], as recorded by NYPL's
   * "What's on the Menu?" volunteers. It marks roughly where the dish's text
   * starts, not a full box.
   */
  pos?: [x: number, y: number]
  /** Index into Restaurant.pages for multi-page menus (default 0). */
  page?: number
  confidence?: number
}

/** One page image of a menu. `src` is a path under public/ or a full http(s) URL. */
export interface ScanPage {
  src: string
  /** Tried once if `src` fails to load (NYPL refuses large sizes for some later menus). */
  fallbackSrc?: string
  width: number
  height: number
  /** Catalogue page for this particular scan, when the host has one. */
  sourceUrl?: string
}

export interface Restaurant {
  id: string
  /** Shared by every menu of the same place (a hotel may have menus from several years). */
  venue?: string
  name: string
  /** Year the menu was printed. Prices are in this year's dollars. */
  year: number
  opened: number
  closed: number | null
  /** false when opened/closed are unknown and only the menu's own year is certain */
  yearsKnown?: boolean
  address: string
  lat: number
  lng: number
  cuisine: string
  emoji: string
  blurb: string
  stillStanding: {
    status: 'open' | 'gone' | 'moved' | 'unknown'
    label: string
    today: string
    /** A few sentences on the building, from the linked sources. */
    history?: string
    sources?: { label: string; url: string }[]
  }
  /** First (or only) page, plus credit details for the whole menu. */
  scan: ScanPage & {
    placeholder: boolean
    credit: string
    sourceUrl?: string
    license?: string
  }
  /** All page images when the menu has more than one; dishes point at these by index. */
  pages?: ScanPage[]
  source?: string
  menu: Dish[]
}

export interface MenusFile {
  version: number
  restaurants: Restaurant[]
}

export interface CpiFile {
  base_year: number
  base_cpi: number
  base_cpi_is_estimate?: boolean
  years: Record<string, { cpi: number; multiplier: number }>
}

export interface LatLng {
  lat: number
  lng: number
}

export interface BagLine {
  dish: Dish
  qty: number
}
