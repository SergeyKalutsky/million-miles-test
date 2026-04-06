import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import type { Car, PaginatedCars } from '../api/types'
import { useAuth } from '../context/AuthContext'
import Navbar from '../components/Navbar'

const PAGE_SIZE = 20

interface Filters {
  brand: string
  body_type: string
  fuel_type: string
  transmission: string
  color: string
  year_min: string
  year_max: string
  price_max: string
}

interface Facets {
  brands: string[]
  body_types: string[]
  fuel_types: string[]
  transmissions: string[]
  colors: string[]
}

const INIT_FILTERS: Filters = {
  brand: '', body_type: '', fuel_type: '', transmission: '', color: '',
  year_min: '', year_max: '', price_max: '',
}

function fmtPrice(v: number | null) {
  if (!v) return '—'
  return `¥${v.toLocaleString()}`
}
function fmtMileage(v: number | null) {
  if (!v) return '—'
  return `${v.toLocaleString()} km`
}

function CarCard({ car }: { car: Car }) {
  const img = car.photos[0]
  return (
    <Link
      to={`/cars/${car.id}`}
      className="group bg-white dark:bg-gray-800 rounded-xl shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all overflow-hidden flex flex-col"
    >
      {img ? (
        <img src={img} alt={`${car.brand} ${car.model}`}
          className="w-full aspect-video object-cover bg-gray-100 dark:bg-gray-700" loading="lazy" />
      ) : (
        <div className="w-full aspect-video bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-4xl text-gray-300">🚗</div>
      )}
      <div className="p-3 flex flex-col flex-1 gap-1">
        <p className="text-xs text-gray-400 uppercase tracking-wide font-medium">{car.brand ?? '—'}</p>
        <p className="font-semibold text-gray-900 dark:text-gray-100 leading-snug line-clamp-2">{car.model ?? 'Unknown model'}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {car.year ?? '—'} · {fmtMileage(car.mileage_km)} · {car.transmission ?? '—'}
        </p>
        <p className="mt-auto pt-2 text-base font-bold text-blue-600 dark:text-blue-400">{fmtPrice(car.price_jpy)}</p>
      </div>
    </Link>
  )
}

function FacetSelect({
  label, value, options, onChange,
}: { label: string; value: string; options: string[]; onChange: (v: string) => void }) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="input-field appearance-none pr-8"
      >
        <option value="">{label}</option>
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
      <span className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-xs">▼</span>
      {value && (
        <button
          onClick={() => onChange('')}
          className="absolute right-7 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-sm leading-none"
          aria-label="Clear"
        >✕</button>
      )}
    </div>
  )
}

export default function CarsPage() {
  const { username, logout } = useAuth()
  const [filters, setFilters] = useState<Filters>(INIT_FILTERS)
  const [sort, setSort] = useState('created_at:desc')
  const [page, setPage] = useState(1)
  const [data, setData] = useState<PaginatedCars | null>(null)
  const [facets, setFacets] = useState<Facets>({ brands: [], body_types: [], fuel_types: [], transmissions: [], colors: [] })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get<Facets>('/cars/facets').then(r => setFacets(r.data)).catch(() => {})
  }, [])

  const fetchCars = useCallback(async (f: Filters, s: string, p: number) => {
    setLoading(true)
    setError('')
    try {
      const [sortField, sortDir] = s.split(':')
      const params: Record<string, string | number> = { page: p, page_size: PAGE_SIZE }
      if (f.brand)        params.brand        = f.brand
      if (f.body_type)    params.body_type    = f.body_type
      if (f.fuel_type)    params.fuel_type    = f.fuel_type
      if (f.transmission) params.transmission = f.transmission
      if (f.color)        params.color        = f.color
      if (f.year_min)     params.year_min     = f.year_min
      if (f.year_max)     params.year_max     = f.year_max
      if (f.price_max)    params.price_max    = f.price_max
      if (sortField)      params.sort_by      = sortField
      if (sortDir)        params.sort_dir     = sortDir
      const { data: res } = await api.get<PaginatedCars>('/cars/', { params })
      setData(res)
    } catch {
      setError('Failed to load cars. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [])

  // Reset to page 1 on filter/sort change, then fetch
  useEffect(() => { setPage(1) }, [filters, sort])
  useEffect(() => { fetchCars(filters, sort, page) }, [filters, sort, page, fetchCars])

  function setFilter(k: keyof Filters) {
    return (v: string) => setFilters(f => ({ ...f, [k]: v }))
  }
  function setFilterEv(k: keyof Filters) {
    return (e: React.ChangeEvent<HTMLInputElement>) => setFilters(f => ({ ...f, [k]: e.target.value }))
  }

  const hasFilters = Object.values(filters).some(Boolean)

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 transition-colors">
      <Navbar username={username} onLogout={logout} />

      <div className="max-w-7xl mx-auto px-4 py-6">

        {/* Filter panel */}
        <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-4 mb-4 border border-gray-100 dark:border-gray-800">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">Filters</p>
            {hasFilters && (
              <button onClick={() => setFilters(INIT_FILTERS)}
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline">
                Clear all
              </button>
            )}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
            <FacetSelect label="Brand"        value={filters.brand}        options={facets.brands}        onChange={setFilter('brand')} />
            <FacetSelect label="Body type"    value={filters.body_type}    options={facets.body_types}    onChange={setFilter('body_type')} />
            <FacetSelect label="Fuel"         value={filters.fuel_type}    options={facets.fuel_types}    onChange={setFilter('fuel_type')} />
            <FacetSelect label="Transmission" value={filters.transmission} options={facets.transmissions} onChange={setFilter('transmission')} />
            <FacetSelect label="Color"        value={filters.color}        options={facets.colors}        onChange={setFilter('color')} />
            <input placeholder="Year from" type="number" value={filters.year_min} onChange={setFilterEv('year_min')} className="input-field" />
            <input placeholder="Year to"   type="number" value={filters.year_max} onChange={setFilterEv('year_max')} className="input-field" />
            <input placeholder="Max price (¥)" type="number" value={filters.price_max} onChange={setFilterEv('price_max')} className="input-field" />
          </div>
        </div>

        {/* Sort + result count bar */}
        <div className="flex items-center justify-between mb-4 px-1">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {data ? <>{data.total.toLocaleString()} cars</> : '…'}
          </p>
          <div className="relative">
            <select value={sort} onChange={e => setSort(e.target.value)}
              className="input-field w-auto pl-3 pr-8 py-1.5 text-xs font-medium appearance-none cursor-pointer">
              <option value="created_at:desc">Newest first</option>
              <option value="price_jpy:asc">Price ↑</option>
              <option value="price_jpy:desc">Price ↓</option>
              <option value="mileage_km:asc">Mileage ↑</option>
              <option value="year:desc">Year ↓</option>
            </select>
            <span className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-xs">▼</span>
          </div>
        </div>

        {/* Results */}
        {error && <div className="text-center py-16 text-red-500">{error}</div>}

        {loading ? (
          <div className="flex justify-center py-24">
            <span className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
          </div>
        ) : data && data.items.length === 0 ? (
          <div className="text-center py-24 text-gray-400">
            <div className="text-5xl mb-3">🔍</div>
            <p>No cars match your filters.</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {(data?.items ?? []).map(car => <CarCard key={car.id} car={car} />)}
          </div>
        )}

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-center gap-2 pt-8 flex-wrap">
            <button disabled={page === 1} onClick={() => setPage(p => p - 1)}
              className="px-3 py-1.5 border border-gray-300 dark:border-gray-700 rounded-lg text-sm disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-800 transition text-gray-700 dark:text-gray-300">
              ← Prev
            </button>
            <span className="text-sm text-gray-500 dark:text-gray-400 px-2">
              Page {data.page} of {data.pages}
            </span>
            <button disabled={page === data.pages} onClick={() => setPage(p => p + 1)}
              className="px-3 py-1.5 border border-gray-300 dark:border-gray-700 rounded-lg text-sm disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-800 transition text-gray-700 dark:text-gray-300">
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
