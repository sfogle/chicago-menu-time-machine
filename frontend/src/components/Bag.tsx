import { useEffect, useState } from 'react'
import type { BagLine, Restaurant } from '../types'
import { roundCents, usd } from '../lib/money'
import { salesTaxFor } from '../lib/tax'

interface Props {
  restaurant: Restaurant | null
  lines: BagLine[]
  multiplier: number
  baseYear: number
  baseIsEstimate: boolean
  onQty: (dishId: string, delta: number) => void
  onClear: () => void
  onClose: () => void
}

const plain = (n: number) => n.toFixed(2)

function Row({ label, value, bold }: { label: string; value: string; bold?: boolean }) {
  return (
    <div className={`flex items-baseline gap-2 ${bold ? 'font-bold' : ''}`}>
      <span>{label}</span>
      <span className="flex-1 border-b border-dotted border-current opacity-40" aria-hidden="true" />
      <span className="tabular-nums">{value}</span>
    </div>
  )
}

export default function Bag({ restaurant, lines, multiplier, baseYear, baseIsEstimate, onQty, onClear, onClose }: Props) {
  const [ordered, setOrdered] = useState<{ year: number; total: number; today: number; name: string } | null>(null)

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const year = restaurant?.year ?? 0
  const tax = salesTaxFor(year)
  const subtotal = roundCents(lines.reduce((sum, l) => sum + l.dish.price * l.qty, 0))
  const taxAmount = roundCents(subtotal * tax.rate)
  const total = roundCents(subtotal + taxAmount)
  const today = roundCents(total * multiplier)

  function placeOrder() {
    if (!restaurant) return
    setOrdered({ year, total, today, name: restaurant.name })
    onClear()
  }

  return (
    <div className="fade-in fixed inset-0 z-[1100] flex justify-end bg-ink/70" onClick={onClose}>
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Delivery bag"
        onClick={(e) => e.stopPropagation()}
        className="slide-left flex h-full w-full max-w-md flex-col bg-ink text-card"
      >
        <header className="flex items-center justify-between p-4">
          <h2 className="font-display text-2xl">🛍️ Delivery Bag</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close bag"
            className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-card text-lg font-bold hover:bg-white/10"
          >
            ✕
          </button>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto px-5 pb-6 pt-3">
          {ordered ? (
            <div className="receipt text-center">
              <p className="stamp text-xl">SENT TO {ordered.year}</p>
              <p className="mt-4 font-bold">Order telegraphed to {ordered.name}.</p>
              <p className="mt-2 text-sm">
                You owe {usd(ordered.total)} in {ordered.year} money, which is {usd(ordered.today)} today. Delivery
                estimate: roughly {baseYear - ordered.year} years ago.
              </p>
              <p className="mt-3 text-xs opacity-70">No real order was placed. Sadly.</p>
            </div>
          ) : !restaurant || lines.length === 0 ? (
            <div className="rounded-2xl border-2 border-dashed border-white/30 p-8 text-center">
              <p className="text-4xl" aria-hidden="true">
                🧾
              </p>
              <p className="mt-2 font-bold">Your bag is empty.</p>
              <p className="mt-1 text-sm text-white/70">Open a restaurant and tap + on anything that looks good.</p>
            </div>
          ) : (
            <div className="receipt text-sm">
              <div className="text-center">
                <p className="font-display text-xl tracking-wide">{restaurant.name}</p>
                <p>{restaurant.address} · Chicago, Ill.</p>
                <p className="mt-1 text-xs uppercase tracking-[0.2em]">Guest check · anno {year}</p>
              </div>
              <div className="receipt-tear" />

              <ul className="space-y-3">
                {lines.map(({ dish, qty }) => (
                  <li key={dish.id}>
                    <Row label={`${qty} × ${dish.name}`} value={plain(dish.price * qty)} />
                    <div className="mt-1 flex items-center gap-2 font-sans text-xs">
                      <button
                        type="button"
                        onClick={() => onQty(dish.id, -1)}
                        aria-label={`Remove one ${dish.name}`}
                        className="h-7 w-7 rounded-full border border-ink/50 font-bold hover:bg-ink/10"
                      >
                        −
                      </button>
                      <button
                        type="button"
                        onClick={() => onQty(dish.id, 1)}
                        aria-label={`Add one more ${dish.name}`}
                        className="h-7 w-7 rounded-full border border-ink/50 font-bold hover:bg-ink/10"
                      >
                        +
                      </button>
                      <span className="opacity-60">@ {plain(dish.price)} each</span>
                    </div>
                  </li>
                ))}
              </ul>

              <div className="receipt-tear" />
              <div className="space-y-1">
                <Row label="Subtotal" value={plain(subtotal)} />
                <Row label={`Ill. sales tax ${(tax.rate * 100).toFixed(tax.rate * 1000 % 10 ? 1 : 0)}%`} value={plain(taxAmount)} />
                <p className="text-xs opacity-60">{tax.note}</p>
                <Row label="Time-travel delivery" value="0.00" />
                <Row label={`TOTAL (${year} dollars)`} value={`$${plain(total)}`} bold />
              </div>

              <div className="receipt-tear" />
              <div className="text-center">
                <p className="text-xs uppercase tracking-[0.2em]">Adjusted for inflation</p>
                <p className="mt-1 text-xs">
                  ${plain(total)} × {multiplier.toFixed(2)} (CPI {year} → {baseYear})
                </p>
                <p className="mt-1 font-display text-4xl text-brick">{usd(today)}</p>
                <p className="text-xs">in {baseYear} dollars{baseIsEstimate ? ' (est.)' : ''}</p>
              </div>
              <div className="receipt-tear" />
              <p className="text-center text-xs uppercase tracking-[0.2em]">Thank you · call again</p>
            </div>
          )}
        </div>

        {!ordered && restaurant && lines.length > 0 && (
          <footer className="flex gap-3 border-t border-white/15 p-4">
            <button type="button" onClick={onClear} className="rounded-xl border-2 border-card px-4 py-3 font-bold hover:bg-white/10">
              Empty
            </button>
            <button type="button" onClick={placeOrder} className="sticker flex-1 rounded-xl bg-mustard py-3 font-bold text-ink">
              Send order to {year} · {usd(today)}
            </button>
          </footer>
        )}
      </aside>
    </div>
  )
}
