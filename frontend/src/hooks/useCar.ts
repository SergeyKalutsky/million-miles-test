import { useState, useEffect } from 'react'
import api from '../api/client'
import type { Car } from '../api/types'

export function useCar(id: string | undefined) {
  const [car, setCar] = useState<Car | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) return
    setLoading(true)
    setError('')
    api.get<Car>(`/cars/${id}`)
      .then(r => setCar(r.data))
      .catch(() => setError('Car not found'))
      .finally(() => setLoading(false))
  }, [id])

  return { car, loading, error }
}
