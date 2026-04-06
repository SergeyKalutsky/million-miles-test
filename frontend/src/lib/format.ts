export function fmtPrice(v: number | null): string {
  if (v == null || v < 0) return '—'
  return `¥${v.toLocaleString()}`
}

export function fmtMileage(v: number | null): string {
  if (v == null) return '—'
  return `${v.toLocaleString()} km`
}
