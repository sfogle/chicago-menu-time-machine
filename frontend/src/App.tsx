import { useCallback, useEffect, useMemo, useState } from 'react'
import type { BagLine, CpiFile, Dish, LatLng, MenusFile, Restaurant } from './types'
import { THE_LOOP, formatMiles, milesBetween } from './lib/geo'
import { menuPrice, multiplierFor, usd } from './lib/money'
import TimeMachineBar from './components/TimeMachineBar'
import MapView from './components/MapView'
import RestaurantCard, { eraNote } from './components/RestaurantCard'
import MenuModal from './components/MenuModal'
import Bag from './components/Bag'

/** Restaurants that opened or closed within this many years still show up as "nearby in time". */
const NEAR_YEARS = 10
/** Beyond this distance from the Loop we assume the visitor is not actually in Chicago. */
const CHICAGO_RADIUS_MI = 40

const dataUrl = (file: string) => `${import.meta.env.BASE_URL}data/${file}`

interface Located {
  point: LatLng
  label: string
}

export default function App() {
  const [restaurants, setRestaurants] = useState<Restaurant[] | null>(null)
  const [cpi, setCpi] = useState<CpiFile | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [year, setYear] = useState(1900)
  const [search, setSearch] = useState('')
  const [view, setView] = useState<'list' | 'map'>('list')
  const [where, setWhere] = useState<Located>({ point: THE_LOOP, label: 'The Loop (default)' })
  const [locating, setLocating] = useState(false)

  const [open, setOpen] = useState<{ restaurant: Restaurant; dishId: string | null } | null>(null)
  const [bagOpen, setBagOpen] = useState(false)
  const [bag, setBag] = useState<{ restaurantId: string | null; lines: BagLine[] }>({ restaurantId: null, lines: [] })
  const [conflict, setConflict] = useState<{ restaurant: Restaurant; dish: Dish } | null>(null)
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    const get = async <T,>(file: string): Promise<T> => {
      const res = await fetch(dataUrl(file))
      if (!res.ok) throw new Error(`${file}: HTTP ${res.status}`)
      return res.json() as Promise<T>
    }
    Promise.all([get<MenusFile>('menus.json'), get<CpiFile>('cpi_chicago.json')])
      .then(([menus, cpiFile]) => {
        setRestaurants(menus.restaurants)
        setCpi(cpiFile)
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
  }, [])

  useEffect(() => {
    if (!toast) return
    const id = window.setTimeout(() => setToast(null), 2200)
    return () => window.clearTimeout(id)
  }, [toast])

  const all = useMemo(() => restaurants ?? [], [restaurants])
  const menuYears = useMemo(() => [...new Set(all.map((r) => r.year))].sort((a, b) => a - b), [all])
  const baseYear = cpi?.base_year ?? 2026

  const miles = useCallback((r: Restaurant) => milesBetween(where.point, r), [where])

  // A venue can have menus from several years (the Congress Hotel has 1907,
  // 1908 and 1912). Show one card per venue: the menu closest to the selected
  // year, with the others offered as year links on the card.
  const { current, otherYears } = useMemo(() => {
    const groups = new Map<string, Restaurant[]>()
    for (const r of all) {
      const key = r.venue ?? `${r.name}|${r.lat}|${r.lng}`
      groups.set(key, [...(groups.get(key) ?? []), r])
    }
    const current: Restaurant[] = []
    const otherYears = new Map<string, number[]>()
    for (const menus of groups.values()) {
      const pick = [...menus].sort((a, b) => Math.abs(a.year - year) - Math.abs(b.year - year) || a.year - b.year)[0]
      current.push(pick)
      otherYears.set(
        pick.id,
        [...new Set(menus.filter((m) => m.year !== pick.year).map((m) => m.year))].sort((a, b) => a - b),
      )
    }
    return { current, otherYears }
  }, [all, year])

  const { openNow, nearby } = useMemo(() => {
    const byDistance = (a: Restaurant, b: Restaurant) => miles(a) - miles(b)
    const openNow = current.filter((r) => eraNote(r, year).open).sort(byDistance)
    const nearby = current
      .filter((r) => {
        if (eraNote(r, year).open) return false
        const gap = year < r.opened ? r.opened - year : year - (r.closed ?? year)
        return gap <= NEAR_YEARS
      })
      .sort(byDistance)
    return { openNow, nearby }
  }, [current, year, miles])

  const onMap = useMemo(() => [...openNow, ...nearby], [openNow, nearby])
  const openIds = useMemo(() => new Set(openNow.map((r) => r.id)), [openNow])

  const query = search.trim().toLowerCase()
  const hits = useMemo(() => {
    if (!query) return []
    return all
      .flatMap((restaurant) =>
        restaurant.menu
          .filter((d) => `${d.name} ${d.description} ${d.category}`.toLowerCase().includes(query))
          .map((dish) => ({ restaurant, dish })),
      )
      .sort((a, b) => a.restaurant.year - b.restaurant.year)
  }, [all, query])

  function locate() {
    if (!('geolocation' in navigator)) {
      setToast('This browser has no GPS. Staying in the Loop.')
      return
    }
    setLocating(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false)
        const point = { lat: pos.coords.latitude, lng: pos.coords.longitude }
        const away = milesBetween(point, THE_LOOP)
        if (away > CHICAGO_RADIUS_MI) {
          setWhere({ point: THE_LOOP, label: 'The Loop' })
          setToast(`You're ${formatMiles(away)} from Chicago, so we dropped you in the Loop.`)
        } else {
          setWhere({ point, label: 'your location' })
        }
      },
      () => {
        setLocating(false)
        setWhere({ point: THE_LOOP, label: 'The Loop (default)' })
        setToast("Couldn't get your location. Staying in the Loop.")
      },
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 60_000 },
    )
  }

  function putInBag(restaurant: Restaurant, dish: Dish, fresh = false) {
    setBag((prev) => {
      const lines = fresh || prev.restaurantId !== restaurant.id ? [] : prev.lines
      const found = lines.find((l) => l.dish.id === dish.id)
      return {
        restaurantId: restaurant.id,
        lines: found
          ? lines.map((l) => (l === found ? { ...l, qty: l.qty + 1 } : l))
          : [...lines, { dish, qty: 1 }],
      }
    })
    setToast(`Added ${dish.name}`)
  }

  function addToBag(restaurant: Restaurant, dish: Dish) {
    // like any delivery app, one restaurant (and therefore one year) per bag
    if (bag.lines.length > 0 && bag.restaurantId !== restaurant.id) setConflict({ restaurant, dish })
    else putInBag(restaurant, dish)
  }

  function changeQty(dishId: string, delta: number) {
    setBag((prev) => {
      const lines = prev.lines
        .map((l) => (l.dish.id === dishId ? { ...l, qty: l.qty + delta } : l))
        .filter((l) => l.qty > 0)
      return { restaurantId: lines.length ? prev.restaurantId : null, lines }
    })
  }

  const closeMenu = useCallback(() => setOpen(null), [])
  const closeBag = useCallback(() => setBagOpen(false), [])
  const clearBag = useCallback(() => setBag({ restaurantId: null, lines: [] }), [])

  const bagRestaurant = all.find((r) => r.id === bag.restaurantId) ?? null
  const bagCount = bag.lines.reduce((n, l) => n + l.qty, 0)
  const bagSubtotal = bag.lines.reduce((n, l) => n + l.dish.price * l.qty, 0)

  return (
    <div className="min-h-dvh pb-24">
      <header className="sticky top-0 z-[900] border-b-2 border-ink bg-card">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-2">
          <span className="text-2xl" aria-hidden="true">
            🕰️
          </span>
          <h1 className="font-display text-lg leading-none sm:text-2xl">
            <span className="text-brick">Chicago</span> Menu Time Machine
          </h1>
          <button
            type="button"
            onClick={() => setBagOpen(true)}
            className="sticker relative ml-auto flex items-center gap-2 rounded-full bg-card px-3 py-1.5 text-sm font-bold"
            aria-label={`Open delivery bag, ${bagCount} item${bagCount === 1 ? '' : 's'}`}
          >
            🛍️ <span className="hidden sm:inline">Bag</span>
            <span className="flex h-6 min-w-6 items-center justify-center rounded-full bg-brick px-1 text-xs text-white">{bagCount}</span>
          </button>
        </div>
      </header>

      <TimeMachineBar year={year} menuYears={menuYears} onYear={setYear} search={search} onSearch={setSearch} />

      <main className="mx-auto max-w-6xl px-4 pt-4">
        {error ? (
          <p role="alert" className="rounded-xl border-2 border-brick bg-card p-4">
            <strong>Couldn't load the menu data.</strong> {error}. Check that <code>public/data/menus.json</code> and{' '}
            <code>cpi_chicago.json</code> exist and are valid JSON.
          </p>
        ) : !restaurants ? (
          <p className="p-8 text-center text-muted">Warming up the flux capacitor…</p>
        ) : query ? (
          <section aria-label="Dish search results">
            <h2 className="font-display text-xl">
              {hits.length} dish{hits.length === 1 ? '' : 'es'} matching “{search.trim()}”
            </h2>
            <p className="text-sm text-muted">Searching every restaurant and year, not just {year}.</p>
            {hits.length === 0 ? (
              <p className="mt-4 rounded-xl border-2 border-dashed border-ink/40 p-6 text-center">
                Nothing on any menu by that name. Try “steak”, “strudel” or “whitefish”.
              </p>
            ) : (
              <ul className="mt-3 grid gap-2 sm:grid-cols-2">
                {hits.map(({ restaurant, dish }) => (
                  <li key={dish.id}>
                    <button
                      type="button"
                      onClick={() => setOpen({ restaurant, dishId: dish.id })}
                      className="flex w-full items-center gap-3 rounded-xl border-2 border-ink bg-card p-3 text-left shadow-[3px_3px_0_var(--color-ink)]"
                    >
                      <span className="text-2xl" aria-hidden="true">
                        {restaurant.emoji}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block font-bold">{dish.name}</span>
                        <span className="block truncate text-sm text-muted">
                          {restaurant.name} · {restaurant.year}
                        </span>
                      </span>
                      <span className="text-right font-mono">
                        <span className="block font-bold">{menuPrice(dish.price)}</span>
                        <span className="block text-xs text-muted">{usd(dish.price * multiplierFor(cpi, restaurant.year))} today</span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-2">
              <div className="mr-auto">
                <h2 className="font-display text-xl">
                  {openNow.length === 0 ? `Nothing open in ${year}` : `${openNow.length} open in ${year}`}
                </h2>
                <p className="text-sm text-muted">Distances from {where.label}</p>
              </div>
              <button
                type="button"
                onClick={locate}
                disabled={locating}
                className="sticker rounded-full bg-lake px-3 py-1.5 text-sm font-bold text-ink disabled:opacity-70"
              >
                📍 {locating ? 'Locating…' : 'Use My Chicago Location'}
              </button>
              <div className="flex overflow-hidden rounded-full border-2 border-ink text-sm font-bold lg:hidden" role="group" aria-label="Switch view">
                {(['list', 'map'] as const).map((v) => (
                  <button
                    key={v}
                    type="button"
                    onClick={() => setView(v)}
                    aria-pressed={view === v}
                    className={`px-3 py-1.5 ${view === v ? 'bg-ink text-card' : 'bg-card'}`}
                  >
                    {v === 'list' ? '☰ List' : '🗺️ Map'}
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              <div className={`space-y-4 ${view === 'list' ? '' : 'hidden lg:block'}`}>
                {openNow.map((r) => (
                  <RestaurantCard
                    key={r.id}
                    restaurant={r}
                    year={year}
                    miles={miles(r)}
                    active={open?.restaurant.id === r.id}
                    onOpen={() => setOpen({ restaurant: r, dishId: null })}
                    otherYears={otherYears.get(r.id) ?? []}
                    onYear={setYear}
                  />
                ))}
                {nearby.length > 0 && (
                  <>
                    <h2 className="pt-2 font-display text-lg text-muted">Nearby in time</h2>
                    {nearby.map((r) => (
                      <RestaurantCard
                        key={r.id}
                        restaurant={r}
                        year={year}
                        miles={miles(r)}
                        active={open?.restaurant.id === r.id}
                        onOpen={() => setOpen({ restaurant: r, dishId: null })}
                        otherYears={otherYears.get(r.id) ?? []}
                        onYear={setYear}
                      />
                    ))}
                  </>
                )}
                {onMap.length === 0 && (
                  <p className="rounded-xl border-2 border-dashed border-ink/40 p-6 text-center">
                    No restaurants in the dataset were around in {year}. Hit 🎲 Random Year or pick another decade.
                  </p>
                )}
              </div>

              <div
                className={`overflow-hidden rounded-2xl border-2 border-ink shadow-[4px_4px_0_var(--color-ink)] lg:sticky lg:top-16 lg:block lg:h-[calc(100dvh-5.5rem)] ${
                  view === 'map' ? 'h-[62dvh]' : 'hidden'
                }`}
              >
                <MapView
                  restaurants={onMap}
                  openIds={openIds}
                  user={where.point}
                  activeId={open?.restaurant.id ?? null}
                  visibleKey={view}
                  onSelect={(r) => setOpen({ restaurant: r, dishId: null })}
                />
              </div>
            </div>
          </>
        )}

        <footer className="mt-10 border-t border-rule pt-4 text-xs text-muted">
          Menus are from the New York Public Library’s volunteer-transcribed “What’s on the Menu?” dataset, the
          Culinary Institute of America’s menu collection, and a few machine-read Internet Archive scans. Scan images load from those libraries’ servers when you open a
          dish. Railroad dining cars are pinned at their Chicago terminal. Inflation uses national CPI-U; tax rates
          are approximate. Map data © OpenStreetMap contributors.
        </footer>
      </main>

      {bagCount > 0 && !bagOpen && !open && (
        <button
          type="button"
          onClick={() => setBagOpen(true)}
          className="sticker fixed inset-x-4 bottom-4 z-[950] mx-auto flex max-w-md items-center justify-between rounded-2xl bg-brick px-4 py-3 font-bold text-white"
        >
          <span>
            View bag · {bagCount} item{bagCount === 1 ? '' : 's'}
          </span>
          <span className="font-mono">{usd(bagSubtotal)}</span>
        </button>
      )}

      {open && (
        <MenuModal
          key={`${open.restaurant.id}:${open.dishId ?? ''}`}
          restaurant={open.restaurant}
          multiplier={multiplierFor(cpi, open.restaurant.year)}
          baseYear={baseYear}
          initialDishId={open.dishId}
          bagQty={(id) => (bag.restaurantId === open.restaurant.id ? (bag.lines.find((l) => l.dish.id === id)?.qty ?? 0) : 0)}
          onAdd={(dish) => addToBag(open.restaurant, dish)}
          onClose={closeMenu}
        />
      )}

      {bagOpen && (
        <Bag
          restaurant={bagRestaurant}
          lines={bag.lines}
          multiplier={multiplierFor(cpi, bagRestaurant?.year ?? baseYear)}
          baseYear={baseYear}
          baseIsEstimate={cpi?.base_cpi_is_estimate ?? false}
          onQty={changeQty}
          onClear={clearBag}
          onClose={closeBag}
        />
      )}

      {conflict && bagRestaurant && (
        <div className="fade-in fixed inset-0 z-[1200] flex items-center justify-center bg-ink/70 p-4" onClick={() => setConflict(null)}>
          <div
            role="alertdialog"
            aria-modal="true"
            aria-label="Start a new bag?"
            onClick={(e) => e.stopPropagation()}
            className="slide-up w-full max-w-sm rounded-2xl border-2 border-ink bg-card p-5"
          >
            <h2 className="font-display text-xl">Start a new bag?</h2>
            <p className="mt-2 text-sm">
              Your bag holds an order from {bagRestaurant.name} ({bagRestaurant.year}). One bag can only travel to one
              year, so adding from {conflict.restaurant.name} ({conflict.restaurant.year}) empties it first.
            </p>
            <div className="mt-4 flex gap-3">
              <button type="button" onClick={() => setConflict(null)} className="flex-1 rounded-xl border-2 border-ink py-2.5 font-bold">
                Keep my bag
              </button>
              <button
                type="button"
                onClick={() => {
                  putInBag(conflict.restaurant, conflict.dish, true)
                  setConflict(null)
                }}
                className="sticker flex-1 rounded-xl bg-brick py-2.5 font-bold text-white"
              >
                New bag
              </button>
            </div>
          </div>
        </div>
      )}

      {toast && (
        <div role="status" className="slide-up fixed left-1/2 top-16 z-[1300] -translate-x-1/2 rounded-full border-2 border-ink bg-mustard px-4 py-2 text-sm font-bold shadow-[3px_3px_0_var(--color-ink)]">
          {toast}
        </div>
      )}
    </div>
  )
}
