import { useEffect, useRef, useState } from 'react'
import type { Dish, Restaurant, ScanPage } from '../types'
import { menuPrice, usd } from '../lib/money'

interface Props {
  restaurant: Restaurant
  dish: Dish
  /** false while the drawer is hidden but kept mounted to hold its images */
  active: boolean
  multiplier: number
  baseYear: number
  onAdd: () => void
  onClose: () => void
}

/** A rectangle in fractions (0-1) of the page. */
interface Region {
  x: number
  y: number
  w: number
  h: number
  /** true = measured box; false = estimated around a single marked point */
  exact: boolean
}

const pct = (n: number) => `${n * 100}%`
const clamp = (n: number, lo: number, hi: number) => Math.min(Math.max(n, lo), hi)

/** Local `scans/...` paths are served from the app's base; full URLs are used as they are. */
export function resolveSrc(src: string): string {
  return /^https?:\/\//i.test(src) ? src : `${import.meta.env.BASE_URL}${src.replace(/^\//, '')}`
}

function pageFor(restaurant: Restaurant, dish: Dish): ScanPage {
  return restaurant.pages?.[dish.page ?? 0] ?? restaurant.scan
}

/**
 * Where the dish sits on its page. OCR'd menus have a pixel box. NYPL's
 * transcriptions have only the point a volunteer clicked, usually on the
 * first words of the dish, so the box is an estimate: one text line tall,
 * starting a little left of the point.
 */
function regionFor(dish: Dish, page: ScanPage): Region | null {
  if (dish.bbox) {
    const [x, y, w, h] = dish.bbox
    return { x: x / page.width, y: y / page.height, w: w / page.width, h: h / page.height, exact: true }
  }
  if (dish.pos) {
    const [px, py] = dish.pos
    const w = 0.48
    const h = (0.04 * page.width) / page.height // about one line of menu text
    return { x: clamp(px - 0.1, 0, 1 - w), y: clamp(py - h / 2, 0, 1 - h), w, h, exact: false }
  }
  return null
}

/**
 * "Original Scan Proof": the dish's line cropped out of the scan, plus the
 * full page with the dish highlighted and scrolled into view.
 *
 * Images load only once this component is on screen. Every page viewed stays
 * mounted, and the crop reuses the already-loaded image, so switching between
 * dishes on the same menu does not hit the image server again.
 */
export default function ScanProof({ restaurant, dish, active, multiplier, baseYear, onAdd, onClose }: Props) {
  const { scan } = restaurant
  const page = pageFor(restaurant, dish)
  const pageIndex = restaurant.pages ? (dish.page ?? 0) : 0
  const pageCount = restaurant.pages?.length ?? 1
  const region = regionFor(dish, page)
  const box = useRef<HTMLDivElement>(null)

  // pages the visitor has looked at, in first-seen order
  const [visited, setVisited] = useState<ScanPage[]>([page])
  if (!visited.includes(page)) setVisited([...visited, page])
  // per page src: which URL is in use, and whether it has finished loading
  const [status, setStatus] = useState<Record<string, { url: string; state: 'loading' | 'ok' | 'failed' }>>({})
  const current = status[page.src] ?? { url: resolveSrc(page.src), state: 'loading' as const }

  function onLoad(p: ScanPage, url: string) {
    setStatus((s) => ({ ...s, [p.src]: { url, state: 'ok' } }))
  }
  function onError(p: ScanPage, url: string) {
    setStatus((s) => {
      const fallback = p.fallbackSrc ? resolveSrc(p.fallbackSrc) : null
      return fallback && fallback !== url
        ? { ...s, [p.src]: { url: fallback, state: 'loading' } }
        : { ...s, [p.src]: { url, state: 'failed' } }
    })
  }

  useEffect(() => {
    if (active && current.state === 'ok') box.current?.scrollIntoView({ block: 'center', behavior: 'smooth' })
  }, [dish.id, active, current.state])

  // crop = the region plus breathing room, clamped to the page
  const crop = region && {
    x: clamp(region.x - 0.02, 0, 1),
    y: clamp(region.y - region.h * (region.exact ? 0.25 : 0.9), 0, 1),
    w: Math.min(region.w + 0.04, 1),
    h: Math.min(region.h * (region.exact ? 1.5 : 2.8), 1),
  }
  if (crop) {
    crop.w = Math.min(crop.w, 1 - crop.x)
    crop.h = Math.min(crop.h, 1 - crop.y)
  }

  return (
    <div className="flex h-full flex-col bg-ink text-card">
      <header className="flex items-start gap-3 border-b border-white/15 p-4">
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg border border-white/40 px-2.5 py-1 text-sm font-bold hover:bg-white/10"
        >
          <span className="lg:hidden">← Menu</span>
          <span className="hidden lg:inline">✕ Close</span>
        </button>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-bold uppercase tracking-widest text-mustard">Original scan proof</p>
          <h3 className="font-display text-lg leading-tight">{dish.name}</h3>
        </div>
        <div className="text-right font-mono">
          <div className="text-lg font-bold">{menuPrice(dish.price)}</div>
          <div className="text-xs text-white/70">
            {usd(dish.price * multiplier)} in {baseYear}
          </div>
        </div>
      </header>

      {crop && (
        <div className="border-b border-white/15 p-4">
          <p className="mb-2 text-xs uppercase tracking-wider text-white/60">
            Cropped from the {restaurant.year} menu{region?.exact ? '' : ' · position approximate'}
          </p>
          {/* ring, not border: aspect-ratio sizes the border box but the image's % offsets use the
              padding box, so a border shifts thin crops by several lines */}
          <div
            className="relative w-full overflow-hidden rounded-md bg-white/10 ring-2 ring-mustard"
            style={{ aspectRatio: `${crop.w * page.width} / ${crop.h * page.height}` }}
          >
            {current.state === 'ok' && (
              // same URL as the full page below, so this comes from the browser's memory cache
              <img
                src={current.url}
                alt={`Cropped scan of the menu line for ${dish.name}`}
                decoding="async"
                className="absolute max-w-none"
                style={{ width: pct(1 / crop.w), left: pct(-crop.x / crop.w), top: pct(-crop.y / crop.h) }}
              />
            )}
          </div>
        </div>
      )}

      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        <p className="mb-2 text-xs uppercase tracking-wider text-white/60">
          Full page{pageCount > 1 ? ` · scan ${pageIndex + 1} of ${pageCount}` : ''}
        </p>
        {visited.map((p) => {
          const s = status[p.src] ?? { url: resolveSrc(p.src), state: 'loading' as const }
          const isCurrent = p === page
          return (
            <div key={p.src} className={isCurrent ? 'relative overflow-hidden rounded-md bg-white/10' : 'hidden'}>
              {s.state === 'failed' ? (
                <p className="p-6 text-center text-sm" role="alert">
                  The scan image could not be loaded from its host. The dish and price above are from the transcription.
                </p>
              ) : (
                <img
                  key={s.url}
                  src={s.url}
                  width={p.width}
                  height={p.height}
                  loading="lazy"
                  decoding="async"
                  onLoad={() => onLoad(p, s.url)}
                  onError={() => onError(p, s.url)}
                  alt={`Scanned ${restaurant.year} menu from ${restaurant.name}`}
                  className="block h-auto w-full"
                />
              )}
              {isCurrent && region && s.state === 'ok' && (
                <>
                  <div
                    ref={box}
                    className="scan-highlight"
                    style={{ left: pct(region.x), top: pct(region.y), width: pct(region.w), height: pct(region.h) }}
                  />
                  {dish.pos && !region.exact && (
                    <div className="scan-pin" style={{ left: pct(dish.pos[0]), top: pct(dish.pos[1]) }} />
                  )}
                </>
              )}
              {isCurrent && s.state === 'loading' && (
                <p className="absolute inset-x-0 top-6 text-center text-sm text-white/70">Loading scan…</p>
              )}
            </div>
          )
        })}
        <p className="mt-3 text-xs text-white/60">
          {scan.placeholder && <strong className="text-mustard">Placeholder scan. </strong>}
          {scan.credit || 'Scan source not recorded.'}
          {(page.sourceUrl ?? scan.sourceUrl) && (
            <>
              {' '}
              <a
                href={page.sourceUrl ?? scan.sourceUrl}
                target="_blank"
                rel="noreferrer"
                className="underline hover:text-white"
              >
                View source
              </a>
            </>
          )}
          <span className="mt-1 block font-mono">
            {dish.bbox
              ? `bbox [x, y, w, h] = [${dish.bbox.join(', ')}] on ${page.width}×${page.height}px`
              : dish.pos
                ? `marked at x ${dish.pos[0]}, y ${dish.pos[1]} (0–1 of the page) · highlight box is estimated`
                : 'No position recorded for this dish.'}
          </span>
        </p>
      </div>

      <footer className="border-t border-white/15 p-4">
        <button type="button" onClick={onAdd} className="sticker w-full rounded-xl bg-mustard py-3 font-bold text-ink">
          Add to bag · {menuPrice(dish.price)}
        </button>
      </footer>
    </div>
  )
}
