import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import Navbar from '../components/Navbar'
import CarCard from '../components/CarCard'
import Pagination from '../components/Pagination'
import BrandMultiSelect from '../components/filters/BrandMultiSelect'
import FacetSelect from '../components/filters/FacetSelect'
import { useCars, useFacets, INIT_FILTERS } from '../hooks/useCars'
import type { Filters } from '../hooks/useCars'

function sanitizeYear(v: string): string {
  const n = parseInt(v, 10)
  return isNaN(n) || n < 1950 || n > 2100 ? '' : String(n)
}
function sanitizePrice(v: string): string {
  const n = parseInt(v, 10)
  return isNaN(n) || n < 0 ? '' : String(n)
}

export default function CarsPage() {
  const { username, logout } = useAuth()
  const [filters, setFilters] = useState<Filters>(INIT_FILTERS)
  // Separate state for number inputs — displayed immediately, debounced into filters
  const [inputValues, setInputValues] = useState({ year_min: '', year_max: '', price_max: '' })
  // Increment to skip the current debounce cycle (e.g. on clearAll)
  const [resetKey, setResetKey] = useState(0)
  const [sort, setSort] = useState('created_at:desc')
  const [page, setPage] = useState(1)
  const topRef = useRef<HTMLDivElement>(null)

  const facets = useFacets()
  const { data, loading, error } = useCars(filters, sort, page)

  // Debounce number inputs — only commit to filters after 500 ms of no typing
  useEffect(() => {
    const t = setTimeout(() => {
      setFilters(f => ({
        ...f,
        year_min:  sanitizeYear(inputValues.year_min),
        year_max:  sanitizeYear(inputValues.year_max),
        price_max: sanitizePrice(inputValues.price_max),
      }))
    }, 500)
    return () => clearTimeout(t)
  // resetKey changes instantly cancel the debounce without committing stale values
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inputValues, resetKey])

  // Reset to page 1 whenever filters or sort change
  useEffect(() => { setPage(1) }, [filters, sort])

  function setFilter<K extends keyof Filters>(k: K) {
    return (v: Filters[K]) => setFilters(f => ({ ...f, [k]: v }))
  }
  function setInputEv(k: keyof typeof inputValues) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setInputValues(iv => ({ ...iv, [k]: e.target.value }))
  }
  function clearAll() {
    setFilters(INIT_FILTERS)
    setInputValues({ year_min: '', year_max: '', price_max: '' })
    setResetKey(k => k + 1)
  }

  function handlePageChange(p: number) {
    setPage(p)
    topRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const hasFilters =
    filters.brands.length > 0 ||
    Object.entries(filters)
      .filter(([k]) => k !== 'brands')
      .some(([, v]) => Boolean(v)) ||
    Object.values(inputValues).some(Boolean)

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-950 transition-colors">
      <Navbar username={username} onLogout={logout} />

      <div ref={topRef} className="content-scroll flex-1 min-h-0">
        <div className="max-w-7xl mx-auto px-4 py-6">

          {/* Filter panel */}
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-4 mb-4 border border-gray-100 dark:border-gray-800">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">Filters</p>
              <button
                onClick={clearAll}
                disabled={!hasFilters}
                className="text-sm px-3 py-1.5 rounded-md border transition font-medium
                  disabled:opacity-30 disabled:cursor-not-allowed
                  border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300
                  hover:bg-red-50 hover:border-red-300 hover:text-red-600
                  dark:hover:bg-red-950 dark:hover:border-red-700 dark:hover:text-red-400"
              >
                ✕ Clear all
              </button>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
              <BrandMultiSelect selected={filters.brands} options={facets.brands} onChange={setFilter('brands')} />
              <FacetSelect placeholder="Body type…"    value={filters.body_type}    options={facets.body_types}    onChange={setFilter('body_type')} />
              <FacetSelect placeholder="Fuel…"         value={filters.fuel_type}    options={facets.fuel_types}    onChange={setFilter('fuel_type')} />
              <FacetSelect placeholder="Transmission…" value={filters.transmission} options={facets.transmissions} onChange={setFilter('transmission')} />
              <FacetSelect placeholder="Color…"        value={filters.color}        options={facets.colors}        onChange={setFilter('color')} />
              <input placeholder="Year from"     type="number" min={1950} max={2100} value={inputValues.year_min}  onChange={setInputEv('year_min')}  className="input-field" />
              <input placeholder="Year to"       type="number" min={1950} max={2100} value={inputValues.year_max}  onChange={setInputEv('year_max')}  className="input-field" />
              <input placeholder="Max price (¥)" type="number" min={0}              value={inputValues.price_max} onChange={setInputEv('price_max')} className="input-field" />
            </div>
          </div>

          {/* Sort + result count bar */}
          <div className="flex items-center justify-between mb-4 px-1">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {data ? <>{data.total.toLocaleString()} cars</> : '…'}
            </p>
            <div className="relative">
              <select
                value={sort}
                onChange={e => setSort(e.target.value)}
                className="input-field w-auto pl-3 pr-8 py-1.5 text-xs font-medium appearance-none cursor-pointer"
              >
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
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {(data?.items ?? []).map(car => <CarCard key={car.id} car={car} />)}
            </div>
          )}

          <Pagination page={page} totalPages={data?.pages ?? 0} onPageChange={handlePageChange} />

        </div>
      </div>
    </div>
  )
}
