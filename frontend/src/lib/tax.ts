/**
 * Combined sales tax a Chicago diner paid on a restaurant bill, by year.
 *
 * Illinois had no sales tax until the Retailers' Occupation Tax of 1933.
 * Chicago's municipal tax arrived in 1955 and the RTA tax in 1979. Rates
 * changed mid-year more than once; each bracket uses the rate in force for
 * most of the period, so treat these as close approximations.
 */
const BRACKETS: { from: number; rate: number; note: string }[] = [
  { from: 0, rate: 0, note: 'No sales tax: Illinois did not levy one until 1933' },
  { from: 1933, rate: 0.02, note: 'Illinois Retailers’ Occupation Tax, 2%' },
  { from: 1935, rate: 0.03, note: 'Illinois sales tax, 3%' },
  { from: 1941, rate: 0.02, note: 'Illinois sales tax, 2%' },
  { from: 1955, rate: 0.03, note: 'Illinois 2.5% + Chicago 0.5%' },
  { from: 1959, rate: 0.035, note: 'Illinois 3% + Chicago 0.5%' },
  { from: 1961, rate: 0.04, note: 'Illinois 3.5% + Chicago 0.5%' },
  { from: 1967, rate: 0.05, note: 'Illinois 4.25% + Chicago 0.75%' },
  { from: 1969, rate: 0.05, note: 'Illinois 4% + Chicago 1%' },
  { from: 1979, rate: 0.06, note: 'Illinois 4% + Chicago 1% + RTA 1%' },
  { from: 1984, rate: 0.07, note: 'Illinois 5% + Chicago 1% + RTA 1%' },
]

export function salesTaxFor(year: number): { rate: number; note: string } {
  let hit = BRACKETS[0]
  for (const b of BRACKETS) if (year >= b.from) hit = b
  return { rate: hit.rate, note: hit.note }
}
