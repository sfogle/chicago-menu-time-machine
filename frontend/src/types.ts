export type BBox = [x: number, y: number, w: number, h: number]

export interface Dish {
  id: string
  name: string
  description: string
  category: string
  price: number
  /** Pixel box on the scan image: [x, y, width, height]. */
  bbox: BBox
  confidence?: number
}

export interface Restaurant {
  id: string
  name: string
  /** Year the menu was printed. Prices are in this year's dollars. */
  year: number
  opened: number
  closed: number | null
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
  }
  scan: {
    src: string
    width: number
    height: number
    placeholder: boolean
    credit: string
  }
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
