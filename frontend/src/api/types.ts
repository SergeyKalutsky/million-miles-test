export interface Car {
  id: number
  external_id: string
  source_url: string
  brand: string | null
  model: string | null
  year: number | null
  mileage_km: number | null
  price_jpy: number | null
  transmission: string | null
  fuel_type: string | null
  body_type: string | null
  color: string | null
  location: string | null
  photos: string[]
  created_at: string
  updated_at: string
}

export interface PaginatedCars {
  total: number
  page: number
  page_size: number
  pages: number
  items: Car[]
}

export interface Token {
  access_token: string
  token_type: string
}
