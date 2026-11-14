import type { LatLng } from '../types'

export const THE_LOOP: LatLng = { lat: 41.8781, lng: -87.6298 }

/** Great-circle distance in miles. */
export function milesBetween(a: LatLng, b: LatLng): number {
  const R = 3958.8
  const rad = (d: number) => (d * Math.PI) / 180
  const dLat = rad(b.lat - a.lat)
  const dLng = rad(b.lng - a.lng)
  const h =
    Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLng / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(h))
}

export function formatMiles(mi: number): string {
  if (mi < 0.1) return `${Math.round(mi * 5280)} ft`
  return `${mi.toFixed(mi < 10 ? 1 : 0)} mi`
}
