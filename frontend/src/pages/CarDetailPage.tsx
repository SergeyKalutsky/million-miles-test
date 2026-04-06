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

function SpecCard({ label, value }: Spec) {
  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4">
      <p className="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-1">{label}</p>
      <p className="font-semibold text-gray-900 dark:text-gray-100">{value}</p>
    </div>
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

  const prev = useCallback(() => setIdx(i => (i - 1 + photos.length) % photos.length), [photos.length])
  const next = useCallback(() => setIdx(i => (i + 1) % photos.length), [photos.length])

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'ArrowLeft')  prev()
      if (e.key === 'ArrowRight') next()
      if (e.key === 'Escape')     onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [prev, next, onClose])

  return (
    <div
      className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center"
      onClick={onClose}
    >
      {/* Main image */}
      <img
        src={photos[idx]}
        alt=""
        className="max-h-[85vh] max-w-[90vw] object-contain rounded-lg shadow-2xl"
        onClick={e => e.stopPropagation()}
      />

      {/* Close */}
      <button
        onClick={onClose}
        className="absolute top-4 right-5 text-white text-3xl leading-none hover:text-gray-300 transition"
        aria-label="Close"
      >✕</button>

      {/* Prev / Next */}
      {photos.length > 1 && (
        <>
          <button
            onClick={e => { e.stopPropagation(); prev() }}
            className="absolute left-4 top-1/2 -translate-y-1/2 text-white text-4xl hover:text-gray-300 transition select-none"
            aria-label="Previous"
          >‹</button>
          <button
            onClick={e => { e.stopPropagation(); next() }}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-white text-4xl hover:text-gray-300 transition select-none"
            aria-label="Next"
          >›</button>
        </>
      )}

      {/* Thumbnail strip */}
      {photos.length > 1 && (
        <div
          className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2 overflow-x-auto max-w-[90vw] px-2 pb-1"
          onClick={e => e.stopPropagation()}
        >
          {photos.map((url, i) => (
            <button key={i} onClick={() => setIdx(i)}
              className={`flex-shrink-0 rounded-md overflow-hidden border-2 transition ${
                i === idx ? 'border-blue-400' : 'border-transparent opacity-60 hover:opacity-100'
              }`}
            >
              <img src={url} alt="" className="w-16 h-11 object-cover" loading="lazy" />
            </button>
          ))}
        </div>
      )}

      {/* Counter */}
      <p className="absolute top-4 left-5 text-white/70 text-sm">{idx + 1} / {photos.length}</p>
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

  // Scroll thumbnail strip with mouse wheel horizontally
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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 transition-colors">
      <Navbar username={username} onLogout={logout} />

      {lightboxOpen && car && (
        <Lightbox
          photos={car.photos}
          initial={activePhoto}
          onClose={() => setLightboxOpen(false)}
        />
      )}

      <div className="max-w-5xl mx-auto px-4 py-6">
        <Link to="/" className="inline-flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:underline mb-4">
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
          <div className="grid lg:grid-cols-2 gap-8">
            {/* Gallery */}
            <div>
              {/* Main image — click opens lightbox */}
              <div
                className="rounded-2xl overflow-hidden bg-gray-100 dark:bg-gray-800 mb-3 cursor-zoom-in"
                style={{ aspectRatio: '16/9' }}
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

              {/* Thumbnail strip — mouse-wheel scrollable */}
              {car.photos.length > 1 && (
                <div
                  className="flex gap-2 overflow-x-auto pb-2 scroll-smooth"
                  style={{ scrollbarWidth: 'thin' }}
                  onWheel={onThumbWheel}
                >
                  {car.photos.map((url, i) => (
                    <button
                      key={i}
                      onClick={() => setActivePhoto(i)}
                      className={`flex-shrink-0 rounded-lg overflow-hidden border-2 transition ${
                        i === activePhoto
                          ? 'border-blue-500'
                          : 'border-transparent opacity-70 hover:opacity-100'
                      }`}
                    >
                      <img src={url} alt="" className="w-24 h-16 object-cover" loading="lazy" />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Info */}
            <div>
              <p className="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide font-semibold mb-1">
                {car.brand ?? '—'}
              </p>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 leading-tight mb-2">
                {car.model ?? 'Unknown model'}
              </h1>
              <p className="text-3xl font-extrabold text-blue-600 dark:text-blue-400 mb-5">
                {fmtPrice(car.price_jpy)}
              </p>

              <div className="grid grid-cols-2 gap-3 mb-6">
                {specs.map(s => <SpecCard key={s.label} {...s} />)}
              </div>

              <a
                href={car.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white font-semibold rounded-xl transition text-sm"
              >
                View on CarSensor ↗
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
