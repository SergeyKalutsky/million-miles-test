interface Props {
  page: number
  totalPages: number
  onPageChange: (page: number) => void
}

function buildPageRange(current: number, total: number): (number | '…')[] {
  const delta = 2
  const range: number[] = []
  for (let i = Math.max(1, current - delta); i <= Math.min(total, current + delta); i++) {
    range.push(i)
  }
  const result: (number | '…')[] = []
  if (range[0] > 1) {
    result.push(1)
    if (range[0] > 2) result.push('…')
  }
  result.push(...range)
  if (range[range.length - 1] < total) {
    if (range[range.length - 1] < total - 1) result.push('…')
    result.push(total)
  }
  return result
}

const BTN_BASE =
  'px-3 py-1.5 border border-gray-300 dark:border-gray-700 rounded-lg text-sm transition text-gray-700 dark:text-gray-300'

export default function Pagination({ page, totalPages, onPageChange }: Props) {
  if (totalPages <= 0) return null

  const pages = buildPageRange(page, totalPages)

  return (
    <div className="flex items-center justify-center gap-2 pt-8 flex-wrap">
      <button
        disabled={page === 1}
        onClick={() => onPageChange(page - 1)}
        className={`${BTN_BASE} disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-800`}
      >
        ← Prev
      </button>

      {pages.map((p, i) =>
        p === '…' ? (
          <span key={`e${i}`} className="px-2 text-gray-400 text-sm select-none">
            …
          </span>
        ) : (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            className={`px-3 py-1.5 rounded-lg text-sm border transition ${
              page === p
                ? 'bg-blue-600 border-blue-600 text-white font-semibold'
                : `${BTN_BASE} hover:bg-gray-50 dark:hover:bg-gray-800`
            }`}
          >
            {p}
          </button>
        ),
      )}

      <button
        disabled={page === totalPages}
        onClick={() => onPageChange(page + 1)}
        className={`${BTN_BASE} disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-800`}
      >
        Next →
      </button>
    </div>
  )
}
