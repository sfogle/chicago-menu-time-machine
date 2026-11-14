import type { CpiFile } from '../types'

export function usd(n: number): string {
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
}

/** Menu-style price: 35¢ under a dollar, $1.65 otherwise. */
export function menuPrice(n: number): string {
  return n < 1 ? `${Math.round(n * 100)}¢` : usd(n)
}

export function multiplierFor(cpi: CpiFile | null, year: number): number {
  if (!cpi) return 1
  const years = Object.keys(cpi.years).map(Number)
  const clamped = Math.min(Math.max(year, Math.min(...years)), Math.max(...years))
  return cpi.years[String(clamped)]?.multiplier ?? 1
}

export const roundCents = (n: number) => Math.round(n * 100) / 100
