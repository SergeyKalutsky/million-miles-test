import { useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { INIT_FILTERS } from './useCars'
import type { Filters } from './useCars'

export interface Query {
  filters: Filters
  sort: string
  page: number
}

export const INIT_QUERY: Query = {
  filters: INIT_FILTERS,
  sort: 'created_at:desc',
  page: 1,
}

// ── Serialise Query → URLSearchParams ────────────────────────────────────────

function toSearchParams(q: Query): URLSearchParams {
  const p = new URLSearchParams()
  if (q.sort !== INIT_QUERY.sort) p.set('sort', q.sort)
  if (q.page !== 1)               p.set('page', String(q.page))
  q.filters.brands.forEach(b => p.append('brand', b))
  if (q.filters.body_type)    p.set('body_type',    q.filters.body_type)
  if (q.filters.fuel_type)    p.set('fuel_type',    q.filters.fuel_type)
  if (q.filters.transmission) p.set('transmission', q.filters.transmission)
  if (q.filters.color)        p.set('color',        q.filters.color)
  if (q.filters.year_min)     p.set('year_min',     q.filters.year_min)
  if (q.filters.year_max)     p.set('year_max',     q.filters.year_max)
  if (q.filters.price_max)    p.set('price_max',    q.filters.price_max)
  return p
}

// ── Deserialise URLSearchParams → Query ──────────────────────────────────────

function fromSearchParams(p: URLSearchParams): Query {
  const page = parseInt(p.get('page') ?? '1', 10)
  return {
    sort: p.get('sort') ?? INIT_QUERY.sort,
    page: isNaN(page) || page < 1 ? 1 : page,
    filters: {
      brands:       p.getAll('brand'),
      body_type:    p.get('body_type')    ?? '',
      fuel_type:    p.get('fuel_type')    ?? '',
      transmission: p.get('transmission') ?? '',
      color:        p.get('color')        ?? '',
      year_min:     p.get('year_min')     ?? '',
      year_max:     p.get('year_max')     ?? '',
      price_max:    p.get('price_max')    ?? '',
    },
  }
}

// ── Hook ─────────────────────────────────────────────────────────────────────

export function useQueryState() {
  const [searchParams, setSearchParams] = useSearchParams()

  const query = fromSearchParams(searchParams)

  const setQuery = useCallback(
    (updater: Query | ((prev: Query) => Query)) => {
      setSearchParams(prev => {
        const current = fromSearchParams(prev)
        const next = typeof updater === 'function' ? updater(current) : updater
        return toSearchParams(next)
      }, { replace: false })
    },
    [setSearchParams],
  )

  return { query, setQuery }
}
