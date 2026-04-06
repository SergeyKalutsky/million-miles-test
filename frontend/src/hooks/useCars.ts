import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import type { PaginatedCars } from '../api/types'

const PAGE_SIZE = 20

export interface Filters {
  brands: string[]
  body_type: string
  fuel_type: string
  transmission: string
  color: string
  year_min: string
  year_max: string
  price_max: string
}

export interface Facets {
  brands: string[]
  body_types: string[]
  fuel_types: string[]
  transmissions: string[]
  colors: string[]
}

export const INIT_FILTERS: Filters = {
  brands: [],
  body_type: '',
  fuel_type: '',
  transmission: '',
  color: '',
  year_min: '',
  year_max: '',
  price_max: '',
}

function buildQueryString(f: Filters, sort: string, page: number): string {
  const [sortField, sortDir] = sort.split(':')
  const qs = new URLSearchParams()
  qs.append('page', String(page))
  qs.append('page_size', String(PAGE_SIZE))
  if (f.body_type)    qs.append('body_type',    f.body_type)
  if (f.fuel_type)    qs.append('fuel_type',    f.fuel_type)
  if (f.transmission) qs.append('transmission', f.transmission)
  if (f.color)        qs.append('color',        f.color)
  if (f.year_min)     qs.append('year_min',     f.year_min)
  if (f.year_max)     qs.append('year_max',     f.year_max)
  if (f.price_max)    qs.append('price_max',    f.price_max)
  if (sortField)      qs.append('sort_by',      sortField)
  if (sortDir)        qs.append('sort_dir',     sortDir)
  f.brands.forEach(b => qs.append('brand', b))
  return qs.toString()
}

export function useCars(filters: Filters, sort: string, page: number) {
  const [data, setData] = useState<PaginatedCars | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetch = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const qs = buildQueryString(filters, sort, page)
      const { data: res } = await api.get<PaginatedCars>(`/cars/?${qs}`)
      setData(res)
    } catch {
      setError('Failed to load cars. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [filters, sort, page])

  useEffect(() => { fetch() }, [fetch])

  return { data, loading, error }
}

export function useFacets() {
  const [facets, setFacets] = useState<Facets>({
    brands: [],
    body_types: [],
    fuel_types: [],
    transmissions: [],
    colors: [],
  })

  useEffect(() => {
    api.get<Facets>('/cars/facets').then(r => setFacets(r.data)).catch(() => {})
  }, [])

  return facets
}
