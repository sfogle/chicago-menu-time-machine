import { useEffect, useRef } from 'react'
import type { Dish, Restaurant } from '../types'
import { menuPrice, usd } from '../lib/money'

interface Props {
  restaurant: Restaurant
  dish: Dish
  multiplier: number
  baseYear: number
  onAdd: () => void
  onClose: () => void
}

const pct = (n: number) => `${n * 100}%`

/**
 * "Original Scan Proof": the dish's line cropped out of the scan, plus the
 * full page with the dish's bounding box highlighted and scrolled into view.
 */
export default function ScanProof({ restaurant, dish, multiplier, baseYear, onAdd, onClose }: Props) {
  const { scan } = restaurant
  const src = `${import.meta.env.BASE_URL}${scan.src}`
  const [x, y, w, h] = dish.bbox
  const box = useRef<HTMLDivElement>(null)

  useEffect(() => {
    box.current?.scrollIntoView({ block: 'center', behavior: 'smooth' })
  }, [dish.id])

  // crop = bbox plus a little breathing room, clamped to the page
  const pad = Math.round(h * 0.25)
  const cx = Math.max(0, x - pad)
  const cy = Math.max(0, y - pad)
  const cw = Math.min(scan.width - cx, w + pad * 2)
  const ch = Math.min(scan.height - cy, h + pad * 2)

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

      <div className="border-b border-white/15 p-4">
        <p className="mb-2 text-xs uppercase tracking-wider text-white/60">Cropped from the {restaurant.year} menu</p>
        <div
          role="img"
          aria-label={`Cropped scan of the menu line for ${dish.name}`}
          className="w-full rounded-md border-2 border-mustard"
          style={{
            aspectRatio: `${cw} / ${ch}`,
            backgroundImage: `url("${src}")`,
            backgroundRepeat: 'no-repeat',
            backgroundSize: `${(scan.width / cw) * 100}% auto`,
            backgroundPosition: `${scan.width === cw ? 0 : (cx / (scan.width - cw)) * 100}% ${
              scan.height === ch ? 0 : (cy / (scan.height - ch)) * 100
            }%`,
          }}
        />
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        <p className="mb-2 text-xs uppercase tracking-wider text-white/60">Full page</p>
        <div className="relative overflow-hidden rounded-md">
          <img
            src={src}
            width={scan.width}
            height={scan.height}
            alt={`Scanned ${restaurant.year} menu from ${restaurant.name}`}
            className="block h-auto w-full"
          />
          <div
            ref={box}
            className="scan-highlight"
            style={{
              left: pct(x / scan.width),
              top: pct(y / scan.height),
              width: pct(w / scan.width),
              height: pct(h / scan.height),
            }}
          />
        </div>
        <p className="mt-3 text-xs text-white/60">
          {scan.placeholder && <strong className="text-mustard">Placeholder scan. </strong>}
          {scan.credit || 'Scan source not recorded.'}
          <span className="mt-1 block font-mono">
            bbox [x, y, w, h] = [{dish.bbox.join(', ')}] on {scan.width}×{scan.height}px
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
