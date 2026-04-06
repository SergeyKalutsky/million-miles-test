import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api/client'
import type { Car } from '../api/types'
import { useAuth } from '../context/AuthContext'
import Navbar from '../components/Navbar'

function fmtPrice(v: number | null) {
  if (!v) return '—'
  return `¥${(v / 10000).toLocaleString('ja-JP', { maximumFractionDigits: 1 })}万 (¥${v.toLocaleString()})`
}
function fmtMileage(v: number | null) {
  if (!v) return '—'
  return `${(v / 10000).toFixed(1)} 万km`
}

interface Spec { label: string; value: string }

function SpecCard({ label, value }: Spec) {
  return (
    <div className="bg-gray-50 rounded-xl p-4">
      <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
      <p className="font-semibold text-gray-900">{value}</p>
    </div>
  )
}

export default function CarDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { username, logout } = useAuth()
  const [car, setCar] = useState<Car | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activePhoto, setActivePhoto] = useState(0)

  useEffect(() => {
    setLoading(true)
    api.get<Car>(`/cars/${id}`)
      .then((r: { data: Car }) => setCar(r.data))
      .catch(() => setError('Car not found'))
      .finally(() => setLoading(false))
  }, [id])

  const specs: Spec[] = car ? [
    { label: 'Year', value: car.year ? String(car.year) : '—' },
    { label: 'Mileage', value: fmtMileage(car.mileage_km) },
    { label: 'Transmission', value: car.transmission ?? '—' },
    { label: 'Fuel', value: car.fuel_type ?? '—' },
    { label: 'Body type', value: car.body_type ?? '—' },
    { label: 'Color', value: car.color ?? '—' },
    { label: 'Location', value: car.location ?? '—' },
  ] : []

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar username={username} onLogout={logout} />

      <div className="max-w-5xl mx-auto px-4 py-6">
        <Link to="/" className="inline-flex items-center gap-1 text-sm text-blue-700 hover:underline mb-4">
          ← Back to listings
        </Link>

        {loading && (
          <div className="flex justify-center py-32">
            <span className="w-12 h-12 border-4 border-blue-200 border-t-blue-700 rounded-full animate-spin" />
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
              <div className="rounded-2xl overflow-hidden aspect-video bg-gray-100 mb-3">
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
              {car.photos.length > 1 && (
                <div className="flex gap-2 overflow-x-auto pb-1">
                  {car.photos.map((url, i) => (
                    <button key={i} onClick={() => setActivePhoto(i)}
                      className={`flex-shrink-0 rounded-lg overflow-hidden border-2 transition ${
                        i === activePhoto ? 'border-blue-600' : 'border-transparent'
                      }`}
                    >
                      <img src={url} alt="" className="w-20 h-14 object-cover" loading="lazy" />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Info */}
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wide font-semibold mb-1">{car.brand ?? '—'}</p>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 leading-tight mb-2">
                {car.model ?? 'Unknown model'}
              </h1>
              <p className="text-3xl font-extrabold text-blue-700 mb-5">{fmtPrice(car.price_jpy)}</p>

              <div className="grid grid-cols-2 gap-3 mb-6">
                {specs.map(s => <SpecCard key={s.label} {...s} />)}
              </div>

              <a
                href={car.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-700 hover:bg-blue-800 text-white font-semibold rounded-xl transition text-sm"
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
