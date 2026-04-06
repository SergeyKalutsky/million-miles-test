import { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import type { Car, PaginatedCars } from '../api/types'
import { useAuth } from '../context/AuthContext'
import Navbar from '../components/Navbar'

const PAGE_SIZE = 20

interface Filters {
  brands: string[]
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
  brands: [], body_type: '', fuel_type: '', transmission: '', color: '',
  year_min: '', year_max: '', price_max: '',
}

function fmtPrice(v: number | null) {
  if (v == null || v < 0) return '—'
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

// Multi-select brand picker with chips
function BrandMultiSelect({
  selected, options, onChange,
}: { selected: string[]; options: string[]; onChange: (v: string[]) => void }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  function toggle(brand: string) {
    if (selected.includes(brand)) onChange(selected.filter(b => b !== brand))
    else onChange([...selected, brand])
  }

  const available = options.filter(o => !selected.includes(o))

  return (
    <div ref={ref} className="relative col-span-2 sm:col-span-1 xl:col-span-2">
      {/* chips + trigger */}
      <div
        className="input-field flex flex-wrap gap-1 min-h-9.5 cursor-pointer items-center"
        onClick={() => setOpen(o => !o)}
      >
        {selected.length === 0 && (
          <span className="text-gray-400 dark:text-gray-500 text-sm select-none">Brand…</span>
        )}
        {selected.map(b => (
          <span
            key={b}
            className="inline-flex items-center gap-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs font-medium px-2 py-0.5 rounded-full"
          >
            {b}
            <button
              type="button"
              onClick={e => { e.stopPropagation(); toggle(b) }}
              className="hover:text-blue-600 dark:hover:text-blue-300 leading-none"
              aria-label={`Remove ${b}`}
            >✕</button>
          </span>
        ))}
        <span className="ml-auto text-gray-400 text-xs pl-1">▼</span>
      </div>

      {/* dropdown */}
      {open && available.length > 0 && (
        <div className="absolute z-50 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-56 overflow-y-auto">
          {available.map(o => (
            <button
              key={o}
              type="button"
              onMouseDown={e => e.preventDefault()}
              onClick={() => { toggle(o); setOpen(false) }}
              className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200"
            >
              {o}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function FacetSelect({
  placeholder, value, options, onChange,
}: { placeholder: string; value: string; options: string[]; onChange: (v: string) => void }) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="input-field appearance-none pr-8"
      >
        <option value="">{placeholder}</option>
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
      <span className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-xs">▼</span>
      {value && (
        <button
          type="button"
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
  const topRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.get<Facets>('/cars/facets').then(r => setFacets(r.data)).catch(() => {})
  }, [])

  const fetchCars = useCallback(async (f: Filters, s: string, p: number) => {
    setLoading(true)
    setError('')
    try {
      const [sortField, sortDir] = s.split(':')
      const params: Record<string, string | number | string[]> = { page: p, page_size: PAGE_SIZE }
      // Send multiple brand values as repeated query params
      if (f.brands.length === 1) params.brand = f.brands[0]
      if (f.body_type)    params.body_type    = f.body_type
      if (f.fuel_type)    params.fuel_type    = f.fuel_type
      if (f.transmission) params.transmission = f.transmission
      if (f.color)        params.color        = f.color
      if (f.year_min)     params.year_min     = f.year_min
      if (f.year_max)     params.year_max     = f.year_max
      // Guard against negative price which causes 422
      if (f.price_max) {
        const v = parseInt(f.price_max, 10)
        if (!isNaN(v) && v >= 0) params.price_max = v
      }
      if (sortField)      params.sort_by      = sortField
      if (sortDir)        params.sort_dir     = sortDir

      // Build URLSearchParams manually so multiple brands become repeated `brand=` params
      const qs = new URLSearchParams()
      for (const [k, v] of Object.entries(params)) {
        if (Array.isArray(v)) v.forEach(item => qs.append(k, item))
        else qs.append(k, String(v))
      }
      if (f.brands.length > 1) {
        f.brands.forEach(b => qs.append('brand', b))
      }

      const { data: res } = await api.get<PaginatedCars>(`/cars/?${qs.toString()}`)
      setData(res)
    } catch {
      setError('Failed to load cars. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [])

  // Reset to page 1 on filter/sort change, then fetch
  useEffect(() => { setPage(1) }, [filters, sort])
  useEffect(() => {
    fetchCars(filters, sort, page)
    topRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [filters, sort, page, fetchCars])

  function setFilter<K extends keyof Filters>(k: K) {
    return (v: Filters[K]) => setFilters(f => ({ ...f, [k]: v }))
  }
  function setFilterEv(k: keyof Filters) {
    return (e: React.ChangeEvent<HTMLInputElement>) => setFilters(f => ({ ...f, [k]: e.target.value }))
  }

  const hasFilters = filters.brands.length > 0 || Object.entries(filters)
    .filter(([k]) => k !== 'brands')
    .some(([, v]) => Boolean(v))

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 transition-colors">
      <Navbar username={username} onLogout={logout} />

      <div ref={topRef} className="max-w-7xl mx-auto px-4 py-6">

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
            <BrandMultiSelect
              selected={filters.brands}
              options={facets.brands}
              onChange={setFilter('brands')}
            />
            <FacetSelect placeholder="Body type…"    value={filters.body_type}    options={facets.body_types}    onChange={setFilter('body_type')} />
            <FacetSelect placeholder="Fuel…"         value={filters.fuel_type}    options={facets.fuel_types}    onChange={setFilter('fuel_type')} />
            <FacetSelect placeholder="Transmission…" value={filters.transmission} options={facets.transmissions} onChange={setFilter('transmission')} />
            <FacetSelect placeholder="Color…"        value={filters.color}        options={facets.colors}        onChange={setFilter('color')} />
            <input placeholder="Year from" type="number" min={1950} max={2100} value={filters.year_min} onChange={setFilterEv('year_min')} className="input-field" />
            <input placeholder="Year to"   type="number" min={1950} max={2100} value={filters.year_max} onChange={setFilterEv('year_max')} className="input-field" />
            <input placeholder="Max price (¥)" type="number" min={0} value={filters.price_max} onChange={setFilterEv('price_max')} className="input-field" />
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
        {data && data.pages > 0 && (
          <div className="flex items-center justify-center gap-2 pt-8 flex-wrap">
            <button
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
              className="px-3 py-1.5 border border-gray-300 dark:border-gray-700 rounded-lg text-sm disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-800 transition text-gray-700 dark:text-gray-300"
            >
              ← Prev
            </button>

            {/* page number buttons — show up to 7 around current page */}
            {(() => {
              const total = data.pages
              const range: number[] = []
              const delta = 2
              for (let i = Math.max(1, page - delta); i <= Math.min(total, page + delta); i++) range.push(i)
              // always include first and last with ellipsis
              const pages: (number | '…')[] = []
              if (range[0] > 1) { pages.push(1); if (range[0] > 2) pages.push('…') }
              pages.push(...range)
              if (range[range.length - 1] < total) { if (range[range.length - 1] < total - 1) pages.push('…'); pages.push(total) }
              return pages.map((p2, i) =>
                p2 === '…'
                  ? <span key={`e${i}`} className="px-2 text-gray-400 text-sm select-none">…</span>
                  : <button
                      key={p2}
                      onClick={() => setPage(p2 as number)}
                      className={`px-3 py-1.5 rounded-lg text-sm border transition ${page === p2
                        ? 'bg-blue-600 border-blue-600 text-white font-semibold'
                        : 'border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'}`}
                    >{p2}</button>
              )
            })()}

            <button
              disabled={page === data.pages}
              onClick={() => setPage(p => p + 1)}
              className="px-3 py-1.5 border border-gray-300 dark:border-gray-700 rounded-lg text-sm disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-800 transition text-gray-700 dark:text-gray-300"
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
