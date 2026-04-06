import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import type { Car } from '../api/types'
import { fmtPrice, fmtMileage } from '../lib/format'

export default function CarCard({ car }: { car: Car }) {
  const img = car.photos[0]
  const { search } = useLocation()
  const [imgLoaded, setImgLoaded] = useState(false)

  return (
    <Link
      to={`/cars/${car.id}`}
      state={{ back: `/${search}` }}
      className="group cursor-pointer bg-white dark:bg-gray-800 rounded-xl shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all overflow-hidden flex flex-col"
    >
      <div className="relative w-full aspect-video bg-gray-100 dark:bg-gray-700 overflow-hidden">
        {/* Shimmer skeleton shown until image loads */}
        {!imgLoaded && img && (
          <div className="skeleton absolute inset-0" />
        )}
        {img ? (
          <img
            src={img}
            alt={`${car.brand} ${car.model}`}
            className={`w-full h-full object-cover transition-opacity duration-300 ${imgLoaded ? 'opacity-100' : 'opacity-0'}`}
            loading="lazy"
            onLoad={() => setImgLoaded(true)}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-4xl text-gray-300">
            🚗
          </div>
        )}
      </div>
      <div className="p-3 flex flex-col flex-1 gap-1">
        <p className="text-xs text-gray-400 uppercase tracking-wide font-medium">{car.brand ?? '—'}</p>
        <p className="font-semibold text-gray-900 dark:text-gray-100 leading-snug line-clamp-2">
          {car.model ?? 'Unknown model'}
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {car.year ?? '—'} · {fmtMileage(car.mileage_km)} · {car.transmission ?? '—'}
        </p>
        <div className="mt-auto pt-2 flex items-center justify-between gap-2 flex-wrap">
          <p className="text-base font-bold text-blue-600 dark:text-blue-400">
            {fmtPrice(car.price_jpy)}
          </p>
          {car.fuel_type && (
            <span className="text-[10px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
              {car.fuel_type}
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}
