import type { Restaurant } from '../types'
import { formatMiles } from '../lib/geo'

const STANDING_STYLE: Record<Restaurant['stillStanding']['status'], { icon: string; cls: string }> = {
  open: { icon: '✅', cls: 'bg-relish/15 text-relish border-relish/40' },
  moved: { icon: '🚚', cls: 'bg-mustard/25 text-ink border-mustard' },
  gone: { icon: '🪦', cls: 'bg-ink/10 text-ink border-ink/30' },
  unknown: { icon: '❓', cls: 'bg-lake/15 text-lake-dark border-lake/50' },
}

/** "Open 1898–today", "Opens in 3 years", "Closed 12 years earlier" */
export function eraNote(r: Restaurant, year: number): { open: boolean; text: string } {
  if (r.yearsKnown === false) {
    // only the menu's date is certain: treat the place as open for a few years either side
    const open = Math.abs(year - r.year) <= 5
    return { open, text: open ? `Serving in ${r.year} · other years unknown` : `Known from ${r.year} only` }
  }
  if (year < r.opened) {
    const n = r.opened - year
    return { open: false, text: `Not open yet · opens in ${n} year${n === 1 ? '' : 's'}` }
  }
  if (r.closed !== null && year > r.closed) {
    const n = year - r.closed
    return { open: false, text: `Closed ${n} year${n === 1 ? '' : 's'} earlier` }
  }
  return { open: true, text: `Open ${r.opened}–${r.closed ?? 'today'}` }
}

interface Props {
  restaurant: Restaurant
  year: number
  miles: number
  active: boolean
  /** years of this venue's other menus, if it has more than one */
  otherYears: number[]
  onYear: (year: number) => void
  onOpen: () => void
}

export default function RestaurantCard({ restaurant: r, year, miles, active, otherYears, onYear, onOpen }: Props) {
  const era = eraNote(r, year)
  const standing = STANDING_STYLE[r.stillStanding.status] ?? STANDING_STYLE.unknown
  const gap = r.year - year

  return (
    <article
      className={`overflow-hidden rounded-2xl border-2 bg-card transition-shadow ${
        active ? 'border-brick shadow-[4px_4px_0_var(--color-brick)]' : 'border-ink shadow-[4px_4px_0_var(--color-ink)]'
      } ${era.open ? '' : 'opacity-90'}`}
    >
      <button type="button" onClick={onOpen} className="flex w-full gap-3 p-3 text-left sm:p-4">
        <div
          className={`flex h-16 w-16 shrink-0 items-center justify-center rounded-xl border-2 border-ink text-3xl ${
            era.open ? 'bg-mustard' : 'bg-rule'
          }`}
          aria-hidden="true"
        >
          {r.emoji}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-display text-xl leading-tight">{r.name}</h3>
            <span className="shrink-0 rounded-full bg-ink px-2 py-0.5 font-mono text-xs font-bold text-card">
              {formatMiles(miles)}
            </span>
          </div>
          <p className="mt-0.5 text-sm text-muted">
            {r.cuisine} · {r.address}
          </p>
          <p className="mt-1 text-sm">{r.blurb}</p>
          <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs font-bold">
            <span className={`rounded-full px-2 py-0.5 ${era.open ? 'bg-relish text-white' : 'bg-rule text-ink'}`}>
              {era.text}
            </span>
            <span className="rounded-full border border-ink/30 px-2 py-0.5">
              {r.year} menu
              {gap !== 0 && <span className="font-normal text-muted"> · {Math.abs(gap)} yr{Math.abs(gap) === 1 ? '' : 's'} {gap > 0 ? 'later' : 'earlier'}</span>}
            </span>
            <span className="rounded-full border border-ink/30 px-2 py-0.5">{r.menu.length} dishes</span>
          </div>
        </div>
      </button>
      {otherYears.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 border-t border-rule px-3 py-2 text-xs sm:px-4">
          <span className="font-bold text-muted">Other menus from here:</span>
          {otherYears.map((y) => (
            <button
              key={y}
              type="button"
              onClick={() => onYear(y)}
              aria-label={`Jump to ${y} to see the ${y} menu`}
              className="rounded-full border border-ink/40 px-2 py-0.5 font-mono font-bold hover:bg-mustard"
            >
              {y}
            </button>
          ))}
        </div>
      )}
      <div className={`flex items-start gap-2 border-t-2 border-dashed px-3 py-2 text-sm sm:px-4 ${standing.cls}`}>
        <span aria-hidden="true">{standing.icon}</span>
        <p>
          <span className="font-bold uppercase tracking-wide">Still standing? {r.stillStanding.label}.</span>{' '}
          <span className="text-ink/80">Today: {r.stillStanding.today}</span>
        </p>
      </div>
    </article>
  )
}
