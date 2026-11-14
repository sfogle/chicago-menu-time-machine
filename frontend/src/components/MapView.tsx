import { useEffect, useRef } from 'react'
import L from 'leaflet'
import type { LatLng, Restaurant } from '../types'

interface Props {
  restaurants: Restaurant[]
  /** ids of restaurants operating in the selected year (highlighted pins) */
  openIds: Set<string>
  user: LatLng
  activeId: string | null
  /** bump to tell the map its container was shown or resized */
  visibleKey: unknown
  onSelect: (r: Restaurant) => void
}

export default function MapView({ restaurants, openIds, user, activeId, visibleKey, onSelect }: Props) {
  const el = useRef<HTMLDivElement>(null)
  const map = useRef<L.Map | null>(null)
  const layer = useRef<L.LayerGroup | null>(null)
  const bounds = useRef<L.LatLngBounds | null>(null)
  const onSelectRef = useRef(onSelect)
  onSelectRef.current = onSelect

  useEffect(() => {
    if (!el.current || map.current) return
    const m = L.map(el.current, { zoomControl: true, attributionControl: true }).setView([user.lat, user.lng], 14)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(m)
    layer.current = L.layerGroup().addTo(m)
    map.current = m
    return () => {
      m.remove()
      map.current = null
    }
    // the map is created once; later position changes are handled below
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const m = map.current
    const group = layer.current
    if (!m || !group) return
    group.clearLayers()

    L.marker([user.lat, user.lng], {
      icon: L.divIcon({ className: '', html: '<div class="tm-you"></div>', iconSize: [18, 18], iconAnchor: [9, 9] }),
      interactive: false,
      keyboard: false,
    }).addTo(group)

    for (const r of restaurants) {
      const cls = ['tm-pin', openIds.has(r.id) ? 'is-open' : '', r.id === activeId ? 'is-active' : ''].join(' ')
      L.marker([r.lat, r.lng], {
        icon: L.divIcon({
          className: '',
          html: `<div class="${cls}"><span>${r.emoji}</span></div>`,
          iconSize: [38, 38],
          iconAnchor: [5, 40],
        }),
        title: `${r.name} (${r.year} menu)`,
        alt: r.name,
      })
        .bindTooltip(`${r.name} · ${r.year}`, { direction: 'top', offset: [14, -40] })
        .on('click', () => onSelectRef.current(r))
        .addTo(group)
    }

    const points: L.LatLngTuple[] = [[user.lat, user.lng], ...restaurants.map((r) => [r.lat, r.lng] as L.LatLngTuple)]
    bounds.current = L.latLngBounds(points).pad(0.25)
    m.fitBounds(bounds.current, { maxZoom: 16, animate: false })
  }, [restaurants, openIds, user, activeId])

  useEffect(() => {
    // Leaflet measures its container on init; re-measure when it becomes visible.
    const id = window.setTimeout(() => {
      map.current?.invalidateSize()
      if (bounds.current) map.current?.fitBounds(bounds.current, { maxZoom: 16, animate: false })
    }, 60)
    return () => window.clearTimeout(id)
  }, [visibleKey])

  return <div ref={el} className="h-full w-full" role="application" aria-label="Map of restaurants" />
}
