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
  sort: string
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
  year_min: '', year_max: '', price_max: '', sort: 'created_at:desc',
}

function fmtPrice(v: number | null) {
  if (!v) return '—'
  return `¥${(v / 10000).toLocaleString('ja-JP', { maximumFractionDigits: 1 })}万`
}
function fmtMileage(v: number | null) {
  if (!v) return '—'
  return `${(v / 10000).toFixed(1)} 万km`
}

function CarCard({ car }: { car: Car }) {
  const img = car.photos[0]
  return (
    <Link
      to={`/cars/${car.id}`}
      className="group bg-white rounded-xl shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all overflow-hidden flex flex-col"
    >
      {img ? (
        <img
          src={img}
          alt={`${car.brand} ${car.model}`}
          className="w-full aspect-video object-cover bg-gray-100"
          loading="lazy"
        />
      ) : (
        <div className="w-full aspect-video bg-gray-100 flex items-center justify-center text-4xl text-gray-300">
          🚗
        </div>
      )}
      <div className="p-3 flex flex-col flex-1 gap-1">
        <p className="text-xs text-gray-400 uppercase tracking-wide font-medium">{car.brand ?? '—'}</p>
        <p className="font-semibold text-gray-900 leading-snug line-clamp-2">{car.model ?? 'Unknown model'}</p>
        <p className="text-xs text-gray-500">
          {car.year ?? '—'} · {fmtMileage(car.mileage_km)} · {car.transmission ?? '—'}
        </p>
        <p className="mt-auto pt-2 text-base font-bold text-blue-700">{fmtPrice(car.price_jpy)}</p>
      </div>
    </Link>
  )
}

function FacetSelect({
  label, value, options, onChange,
}: { label: string; value: string; options: string[]; onChange: (v: string) => void }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)} className="input-field">
      <option value="">{label}</option>
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  )
}

export default function CarsPage() {
  const { username, logout } = useAuth()
  const [filters, setFilters] = useState<Filters>(INIT_FILTERS)
  const [applied, setApplied] = useState<Filters>(INIT_FILTERS)
  const [page, setPage] = useState(1)
  const [data, setData] = useState<PaginatedCars | null>(null)
  const [facets, setFacets] = useState<Facets>({ brands: [], body_types: [], fuel_types: [], transmissions: [], colors: [] })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Load facets once on mount
  useEffect(() => {
    api.get<Facets>('/cars/facets').then(r => setFacets(r.data)).catch(() => {})
  }, [])

  const fetchCars = useCallback(async (f: Filters, p: number) => {
    setLoading(true)
    setError('')
    try {
      const [sortField, sortDir] = f.sort.split(':')
      const params: Record<string, string | number> = { page: p, page_size: PAGE_SIZE }
      if (f.brand) params.brand = f.brand
      if (f.body_type) params.body_type = f.body_type
      if (f.fuel_type) params.fuel_type = f.fuel_type
      if (f.transmission) params.transmission = f.transmission
      if (f.color) params.color = f.color
      if (f.year_min) params.year_min = f.year_min
      if (f.year_max) params.year_max = f.year_max
      if (f.price_max) params.price_max = f.price_max
      if (sortField) params.sort_by = sortField
      if (sortDir) params.sort_dir = sortDir
      const { data: res } = await api.get<PaginatedCars>('/cars/', { params })
      setData(res)
    } catch {
      setError('Failed to load cars. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchCars(applied, page) }, [applied, page, fetchCars])

  function applyFilters() { setPage(1); setApplied({ ...filters }) }
  function resetFilters() { setFilters(INIT_FILTERS); setPage(1); setApplied(INIT_FILTERS) }

  const set = (k: keyof Filters) => (v: string) => setFilters(f => ({ ...f, [k]: v }))
  const setEv = (k: keyof Filters) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setFilters(f => ({ ...f, [k]: e.target.value }))

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar username={username} onLogout={logout} />

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            <FacetSelect label="Brand"        value={filters.brand}        options={facets.brands}        onChange={set('brand')} />
            <FacetSelect label="Body type"    value={filters.body_type}    options={facets.body_types}    onChange={set('body_type')} />
            <FacetSelect label="Fuel type"    value={filters.fuel_type}    options={facets.fuel_types}    onChange={set('fuel_type')} />
            <FacetSelect label="Transmission" value={filters.transmission} options={facets.transmissions} onChange={set('transmission')} />
            <FacetSelect label="Color"        value={filters.color}        options={facets.colors}        onChange={set('color')} />
            <input placeholder="Year from" type="number" value={filters.year_min} onChange={setEv('year_min')}
              className="input-field" />
            <input placeholder="Year to" type="number" value={filters.year_max} onChange={setEv('year_max')}
              className="input-field" />
            <input placeholder="Max price (¥)" type="number" value={filters.price_max} onChange={setEv('price_max')}
              className="input-field" />
            <select value={filters.sort} onChange={setEv('sort')} className="input-field">
              <option value="created_at:desc">Newest first</option>
              <option value="price_jpy:asc">Price ↑</option>
              <option value="price_jpy:desc">Price ↓</option>
              <option value="mileage_km:asc">Mileage ↑</option>
              <option value="year:desc">Year ↓</option>
            </select>
          </div>
          <div className="flex gap-2 mt-3">
            <button onClick={applyFilters}
              className="px-4 py-2 bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold rounded-lg transition">
              Search
            </button>
            <button onClick={resetFilters}
              className="px-4 py-2 border border-gray-300 hover:bg-gray-50 text-sm font-medium rounded-lg transition">
              Reset
            </button>
          </div>
        </div>

        {/* Results */}
        {error && (
          <div className="text-center py-16 text-red-600">{error}</div>
        )}

        {loading ? (
          <div className="flex justify-center py-24">
            <span className="w-10 h-10 border-4 border-blue-200 border-t-blue-700 rounded-full animate-spin" />
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
            <button
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm disabled:opacity-40 hover:bg-gray-50 transition"
            >
              ← Prev
            </button>
            <span className="text-sm text-gray-500 px-2">
              Page {data.page} of {data.pages} — {data.total.toLocaleString()} cars
            </span>
            <button
              disabled={page === data.pages}
              onClick={() => setPage(p => p + 1)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm disabled:opacity-40 hover:bg-gray-50 transition"
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
