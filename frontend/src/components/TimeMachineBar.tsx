import { useEffect, useRef, useState } from 'react'

export const MIN_YEAR = 1890
export const MAX_YEAR = 1985
const DECADES = [1890, 1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980]

interface Props {
  year: number
  /** Years that have a menu in the dataset; the random button draws from these. */
  menuYears: number[]
  onYear: (year: number) => void
  search: string
  onSearch: (q: string) => void
}

export default function TimeMachineBar({ year, menuYears, onYear, search, onSearch }: Props) {
  const [display, setDisplay] = useState(year)
  const [rolling, setRolling] = useState(false)
  const [landed, setLanded] = useState(0)
  const timer = useRef<number | undefined>(undefined)

  useEffect(() => {
    if (!rolling) setDisplay(year)
  }, [year, rolling])

  useEffect(() => () => window.clearInterval(timer.current), [])

  function spin() {
    if (rolling || menuYears.length === 0) return
    const pool = menuYears.length > 1 ? menuYears.filter((y) => y !== year) : menuYears
    const target = pool[Math.floor(Math.random() * pool.length)]

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      onYear(target)
      return
    }
    setRolling(true)
    let ticks = 0
    timer.current = window.setInterval(() => {
      ticks += 1
      setDisplay(MIN_YEAR + Math.floor(Math.random() * (MAX_YEAR - MIN_YEAR + 1)))
      if (ticks >= 18) {
        window.clearInterval(timer.current)
        setDisplay(target)
        setRolling(false)
        setLanded((n) => n + 1)
        onYear(target)
      }
    }, 65)
  }

  function pickDecade(decade: number) {
    // land on a year with a menu if the decade has one, otherwise mid-decade
    const withMenu = menuYears.find((y) => y >= decade && y < decade + 10)
    onYear(withMenu ?? Math.min(decade + 5, MAX_YEAR))
  }

  const decade = Math.floor(year / 10) * 10

  return (
    <section className="bg-brick text-white" aria-label="Time machine controls">
      <div className="mx-auto max-w-6xl px-4 pb-4 pt-3">
        <div className="flex items-center gap-3">
          <div
            key={landed}
            className={`flex gap-1 text-4xl sm:text-5xl ${rolling ? 'slot-rolling' : 'slot-landed'}`}
            role="status"
            aria-live="polite"
            aria-label={`Selected year ${rolling ? 'spinning' : display}`}
          >
            {String(display)
              .split('')
              .map((d, i) => (
                <span key={i} className="slot-digit" aria-hidden="true">
                  {d}
                </span>
              ))}
          </div>
          <button
            type="button"
            onClick={spin}
            disabled={rolling}
            className="sticker ml-auto rounded-xl bg-mustard px-4 py-3 text-base font-bold text-ink disabled:opacity-80 sm:px-6 sm:text-lg"
          >
            <span className={rolling ? 'inline-block animate-spin' : 'inline-block'}>🎲</span> Random Year
          </button>
        </div>

        <div className="no-scrollbar -mx-4 mt-3 flex gap-2 overflow-x-auto px-4 pb-1" role="group" aria-label="Pick a decade">
          {DECADES.map((d) => (
            <button
              key={d}
              type="button"
              onClick={() => pickDecade(d)}
              aria-pressed={d === decade}
              className={`shrink-0 rounded-full border-2 px-3 py-1 text-sm font-bold transition-colors ${
                d === decade
                  ? 'border-ink bg-card text-ink'
                  : 'border-white/50 text-white hover:border-white hover:bg-white/10'
              }`}
            >
              {d}s
            </button>
          ))}
        </div>

        <label className="mt-2 flex items-center gap-3 text-xs font-bold uppercase tracking-wider text-white/85">
          <span className="shrink-0">Fine-tune</span>
          <input
            type="range"
            min={MIN_YEAR}
            max={MAX_YEAR}
            value={year}
            onChange={(e) => onYear(Number(e.target.value))}
            className="h-2 w-full accent-mustard"
            aria-label="Year"
          />
          <span className="shrink-0 font-mono text-sm tabular-nums">{year}</span>
        </label>

        <div className="relative mt-3">
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2" aria-hidden="true">
            🔎
          </span>
          <input
            type="search"
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            placeholder="Search every era for a dish… schnitzel, whitefish, mai tai"
            aria-label="Search dishes across all years"
            className="w-full rounded-xl border-2 border-ink bg-card py-2.5 pl-10 pr-3 text-base text-ink placeholder:text-muted"
          />
        </div>
      </div>
    </section>
  )
}
