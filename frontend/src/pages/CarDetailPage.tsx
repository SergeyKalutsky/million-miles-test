import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api/client'
import type { Car } from '../api/types'
import { useAuth } from '../context/AuthContext'
import Navbar from '../components/Navbar'

function fmtPrice(v: number | null) {
  if (!v) return '—'
  return `¥${v.toLocaleString()}`
}
function fmtMileage(v: number | null) {
  if (!v) return '—'
  return `${v.toLocaleString()} km`
}

interface Spec { label: string; value: string }

function SpecRow({ label, value }: Spec) {
  return (
    <>
      <dt className="text-xs font-medium uppercase tracking-wide text-gray-400 dark:text-gray-500 py-2 pr-4 border-b border-gray-100 dark:border-gray-800">{label}</dt>
      <dd className="text-sm font-semibold text-gray-900 dark:text-gray-100 py-2 border-b border-gray-100 dark:border-gray-800">{value}</dd>
    </>
  )
}

// ── Lightbox modal ────────────────────────────────────────────────────────────
interface LightboxProps {
  photos: string[]
  initial: number
  onClose: () => void
}

function Lightbox({ photos, initial, onClose }: LightboxProps) {
  const [idx, setIdx] = useState(initial)
  const [loaded, setLoaded] = useState(false)

  const prev = useCallback(() => { setLoaded(false); setIdx(i => (i - 1 + photos.length) % photos.length) }, [photos.length])
  const next = useCallback(() => { setLoaded(false); setIdx(i => (i + 1) % photos.length) }, [photos.length])

  // Keyboard navigation
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'ArrowLeft')  prev()
      if (e.key === 'ArrowRight') next()
      if (e.key === 'Escape')     onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [prev, next, onClose])

  // Preload only prev + next neighbors — not all images
  useEffect(() => {
    const neighbors = [
      (idx - 1 + photos.length) % photos.length,
      (idx + 1) % photos.length,
    ]
    neighbors.forEach(i => { const img = new Image(); img.src = photos[i] })
  }, [idx, photos])

  return (
    <div
      className="fixed inset-0 z-50 bg-black/92 flex items-center justify-center"
      onClick={onClose}
    >
      {/* Spinner shown until image loads */}
      {!loaded && (
        <span className="absolute w-10 h-10 border-4 border-white/20 border-t-white rounded-full animate-spin pointer-events-none" />
      )}

      {/* Current image only — virtualized: only 1 img element in DOM */}
      <img
        key={idx}
        src={photos[idx]}
        alt=""
        onLoad={() => setLoaded(true)}
        className={`max-h-[80vh] max-w-[calc(100vw-7rem)] object-contain rounded-lg shadow-2xl pointer-events-none select-none transition-opacity duration-150 ${loaded ? 'opacity-100' : 'opacity-0'}`}
      />

      {/* Close button */}
      <button
        onClick={e => { e.stopPropagation(); onClose() }}
        aria-label="Close"
        className="absolute top-3 right-3 z-10 w-10 h-10 flex items-center justify-center rounded-full bg-white/10 hover:bg-white/25 transition text-white"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" className="w-5 h-5">
          <path d="M18 6 6 18M6 6l12 12"/>
        </svg>
      </button>

      {/* Counter */}
      <p className="absolute top-4 left-4 z-10 text-white/60 text-sm tabular-nums select-none">
        {idx + 1} / {photos.length}
      </p>

      {/* Prev / Next — SVG chevron buttons */}
      {photos.length > 1 && (
        <>
          <button
            onClick={e => { e.stopPropagation(); prev() }}
            aria-label="Previous"
            className="absolute left-3 top-1/2 -translate-y-1/2 z-10 w-11 h-11 flex items-center justify-center rounded-full bg-white/10 hover:bg-white/25 transition text-white"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
              <path d="M15 18l-6-6 6-6"/>
            </svg>
          </button>
          <button
            onClick={e => { e.stopPropagation(); next() }}
            aria-label="Next"
            className="absolute right-3 top-1/2 -translate-y-1/2 z-10 w-11 h-11 flex items-center justify-center rounded-full bg-white/10 hover:bg-white/25 transition text-white"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
              <path d="M9 18l6-6-6-6"/>
            </svg>
          </button>
        </>
      )}

      {/* Thumbnail strip — lazy loaded, only visible ones */}
      {photos.length > 1 && (
        <div
          className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 flex gap-2 overflow-x-auto max-w-[calc(100vw-6rem)] px-2 pb-1"
          style={{ scrollbarWidth: 'none' }}
          onClick={e => e.stopPropagation()}
        >
          {photos.map((url, i) => (
            <button
              key={i}
              onClick={() => { setLoaded(false); setIdx(i) }}
              className={`shrink-0 rounded-md overflow-hidden border-2 transition-all ${
                i === idx ? 'border-blue-400 opacity-100' : 'border-transparent opacity-50 hover:opacity-80'
              }`}
            >
              <img src={url} alt="" className="w-16 h-11 object-cover" loading="lazy" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function CarDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { username, logout } = useAuth()
  const [car, setCar] = useState<Car | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activePhoto, setActivePhoto] = useState(0)
  const [lightboxOpen, setLightboxOpen] = useState(false)

  useEffect(() => {
    setLoading(true)
    api.get<Car>(`/cars/${id}`)
      .then((r: { data: Car }) => setCar(r.data))
      .catch(() => setError('Car not found'))
      .finally(() => setLoading(false))
  }, [id])

  function onThumbWheel(e: React.WheelEvent<HTMLDivElement>) {
    e.currentTarget.scrollLeft += e.deltaY
  }

  const specs: Spec[] = car ? [
    { label: 'Year',         value: car.year          ? String(car.year) : '—' },
    { label: 'Mileage',      value: fmtMileage(car.mileage_km) },
    { label: 'Transmission', value: car.transmission  ?? '—' },
    { label: 'Fuel',         value: car.fuel_type     ?? '—' },
    { label: 'Body type',    value: car.body_type     ?? '—' },
    { label: 'Color',        value: car.color         ?? '—' },
    { label: 'Location',     value: car.location      ?? '—' },
  ] : []

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-950 transition-colors">
      <Navbar username={username} onLogout={logout} />

      {lightboxOpen && car && (
        <Lightbox
          photos={car.photos}
          initial={activePhoto}
          onClose={() => setLightboxOpen(false)}
        />
      )}

      <div className="content-scroll flex-1 min-h-0">
        <div className="max-w-5xl mx-auto px-4 py-6">
          <Link to="/" className="inline-flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:underline mb-5">
            ← Back to listings
          </Link>

          {loading && (
            <div className="flex justify-center py-32">
              <span className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
            </div>
          )}

          {error && (
            <div className="text-center py-32 text-gray-400">
              <div className="text-5xl mb-3">😕</div>
              <p>{error}</p>
            </div>
          )}

          {car && (
            <div className="grid lg:grid-cols-2 gap-6 lg:gap-10 min-w-0">
              {/* ── Gallery ── */}
              <div className="min-w-0">
                {/* Main image */}
                <div
                  className="w-full rounded-2xl overflow-hidden bg-gray-100 dark:bg-gray-800 mb-3 cursor-zoom-in"
                  style={{ aspectRatio: '4/3', maxHeight: '320px' }}
                  onClick={() => car.photos.length > 0 && setLightboxOpen(true)}
                >
                  {car.photos[activePhoto] ? (
                    <img
                      src={car.photos[activePhoto]}
                      alt={`${car.brand} ${car.model}`}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-6xl text-gray-200">🚗</div>
                  )}
                </div>

                {/* Thumbnail strip */}
                {car.photos.length > 1 && (
                  <div
                    className="flex gap-2 overflow-x-auto pb-1 content-scroll"
                    onWheel={onThumbWheel}
                  >
                    {car.photos.map((url, i) => (
                      <button
                        key={i}
                        onClick={() => setActivePhoto(i)}
                        className={`shrink-0 rounded-lg overflow-hidden border-2 transition ${
                          i === activePhoto
                            ? 'border-blue-500'
                            : 'border-transparent opacity-60 hover:opacity-100'
                        }`}
                      >
                        <img src={url} alt="" className="w-20 h-14 object-cover" loading="lazy" />
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* ── Info ── */}
              <div>
                <p className="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide font-semibold mb-1">
                  {car.brand ?? '—'}
                </p>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 leading-tight mb-1">
                  {car.model ?? 'Unknown model'}
                </h1>
                <p className="text-3xl font-extrabold text-blue-600 dark:text-blue-400 mb-5">
                  {fmtPrice(car.price_jpy)}
                </p>

                <dl className="grid grid-cols-[auto_1fr] mb-5">
                  {specs.map(s => <SpecRow key={s.label} {...s} />)}
                </dl>

                <a
                  href={car.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white font-semibold rounded-lg transition text-sm"
                >
                  View on CarSensor ↗
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
