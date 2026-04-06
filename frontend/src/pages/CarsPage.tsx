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
  year_min: string
  year_max: string
  price_max: string
  sort: string
}

const INIT_FILTERS: Filters = {
  brand: '', body_type: '', fuel_type: '', transmission: '',
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

export default function CarsPage() {
  const { username, logout } = useAuth()
  const [filters, setFilters] = useState<Filters>(INIT_FILTERS)
  const [applied, setApplied] = useState<Filters>(INIT_FILTERS)
  const [page, setPage] = useState(1)
  const [data, setData] = useState<PaginatedCars | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

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

  const set = (k: keyof Filters) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setFilters(f => ({ ...f, [k]: e.target.value }))

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar username={username} onLogout={logout} />

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            <input placeholder="Brand" value={filters.brand} onChange={set('brand')}
              className="input-field" />
            <select value={filters.body_type} onChange={set('body_type')} className="input-field">
              <option value="">Body type</option>
              {['sedan','SUV','hatchback','minivan','compact','coupe','convertible','station wagon','kei car'].map(t =>
                <option key={t} value={t}>{t}</option>)}
            </select>
            <select value={filters.fuel_type} onChange={set('fuel_type')} className="input-field">
              <option value="">Fuel type</option>
              {['gasoline','diesel','hybrid','electric','PHEV'].map(t =>
                <option key={t} value={t}>{t}</option>)}
            </select>
            <select value={filters.transmission} onChange={set('transmission')} className="input-field">
              <option value="">Transmission</option>
              {['AT','MT','CVT','DCT','Semi-AT'].map(t =>
                <option key={t} value={t}>{t}</option>)}
            </select>
            <input placeholder="Year from" type="number" value={filters.year_min} onChange={set('year_min')}
              className="input-field" />
            <input placeholder="Year to" type="number" value={filters.year_max} onChange={set('year_max')}
              className="input-field" />
            <input placeholder="Max price (¥)" type="number" value={filters.price_max} onChange={set('price_max')}
              className="input-field" />
            <select value={filters.sort} onChange={set('sort')} className="input-field">
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
