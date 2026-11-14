import { useEffect, useMemo, useState } from 'react'
import type { Dish, Restaurant } from '../types'
import { menuPrice, usd } from '../lib/money'
import ScanProof from './ScanProof'

interface Props {
  restaurant: Restaurant
  multiplier: number
  baseYear: number
  /** open straight to this dish's scan proof (used by search results) */
  initialDishId: string | null
  bagQty: (dishId: string) => number
  onAdd: (dish: Dish) => void
  onClose: () => void
}

export default function MenuModal({ restaurant, multiplier, baseYear, initialDishId, bagQty, onAdd, onClose }: Props) {
  const [dishId, setDishId] = useState<string | null>(initialDishId)
  const dish = restaurant.menu.find((d) => d.id === dishId) ?? null

  const categories = useMemo(() => {
    const groups = new Map<string, Dish[]>()
    for (const d of restaurant.menu) {
      groups.set(d.category, [...(groups.get(d.category) ?? []), d])
    }
    return [...groups.entries()]
  }, [restaurant])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return
      if (dishId) setDishId(null)
      else onClose()
    }
    window.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }, [dishId, onClose])

  return (
    <div className="fade-in fixed inset-0 z-[1000] flex items-end justify-center bg-ink/70 lg:items-center lg:p-6" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`${restaurant.name} menu, ${restaurant.year}`}
        onClick={(e) => e.stopPropagation()}
        className={`slide-up relative flex h-[94dvh] w-full overflow-hidden rounded-t-3xl border-2 border-ink bg-paper lg:h-[88vh] lg:rounded-3xl ${
          dish ? 'lg:max-w-6xl' : 'lg:max-w-2xl'
        }`}
      >
        {/* menu column */}
        <div className="flex min-w-0 flex-1 flex-col">
          <header className="flex items-start gap-3 border-b-2 border-ink bg-card p-4">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl border-2 border-ink bg-mustard text-3xl" aria-hidden="true">
              {restaurant.emoji}
            </div>
            <div className="min-w-0 flex-1">
              <h2 className="font-display text-2xl leading-tight">{restaurant.name}</h2>
              <p className="text-sm text-muted">
                {restaurant.address} · menu of {restaurant.year}
              </p>
              <p className="mt-0.5 font-mono text-xs text-muted">
                $1.00 in {restaurant.year} ≈ {usd(multiplier)} in {baseYear}
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close menu"
              className="sticker flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-card text-lg font-bold"
            >
              ✕
            </button>
          </header>

          <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-8">
            <p className="pt-3 text-sm text-muted">Tap a dish to see it on the original scan.</p>
            {categories.map(([category, dishes]) => (
              <section key={category} aria-label={category}>
                <h3 className="sticky top-0 z-10 -mx-4 mt-3 border-y border-rule bg-paper/95 px-4 py-1.5 text-sm font-bold uppercase tracking-widest text-brick backdrop-blur">
                  {category}
                </h3>
                <ul>
                  {dishes.map((d) => {
                    const qty = bagQty(d.id)
                    const selected = d.id === dishId
                    return (
                      <li
                        key={d.id}
                        className={`flex items-center gap-2 border-b border-dashed border-rule ${selected ? '-mx-2 rounded-lg bg-mustard/30 px-2' : ''}`}
                      >
                        <button
                          type="button"
                          onClick={() => setDishId(d.id)}
                          aria-pressed={selected}
                          className="flex min-w-0 flex-1 items-baseline gap-2 py-3 text-left"
                        >
                          <span className="min-w-0">
                            <span className="font-bold">{d.name}</span>
                            {d.description && <span className="block text-sm italic text-muted">{d.description}</span>}
                          </span>
                          <span className="mb-1 min-w-4 flex-1 border-b-2 border-dotted border-ink/30" aria-hidden="true" />
                          <span className="shrink-0 text-right font-mono">
                            <span className="font-bold">{menuPrice(d.price)}</span>
                            <span className="block text-xs text-muted">{usd(d.price * multiplier)} today</span>
                          </span>
                        </button>
                        <button
                          type="button"
                          onClick={() => onAdd(d)}
                          aria-label={`Add ${d.name} to bag`}
                          className="sticker relative flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brick text-xl font-bold text-white"
                        >
                          +
                          {qty > 0 && (
                            <span className="absolute -right-1.5 -top-1.5 flex h-5 min-w-5 items-center justify-center rounded-full border-2 border-ink bg-mustard px-1 text-xs text-ink">
                              {qty}
                            </span>
                          )}
                        </button>
                      </li>
                    )
                  })}
                </ul>
              </section>
            ))}
          </div>
        </div>

        {/* scan proof: covers the menu on phones, sits beside it on desktop */}
        {dish && (
          <aside
            aria-label="Original scan proof"
            className="slide-left absolute inset-0 z-20 lg:static lg:w-1/2 lg:shrink-0 lg:border-l-2 lg:border-ink"
          >
            <ScanProof
              restaurant={restaurant}
              dish={dish}
              multiplier={multiplier}
              baseYear={baseYear}
              onAdd={() => onAdd(dish)}
              onClose={() => setDishId(null)}
            />
          </aside>
        )}
      </div>
    </div>
  )
}
