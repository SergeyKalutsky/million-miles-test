import axios, { type InternalAxiosRequestConfig } from 'axios'

const api = axios.create({
  baseURL: (import.meta as ImportMeta & { env: Record<string, string> }).env.VITE_API_URL ?? '/api',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default api
