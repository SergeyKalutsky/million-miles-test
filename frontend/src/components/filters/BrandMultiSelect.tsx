import { useDropdown } from '../../hooks/useDropdown'

interface Props {
  selected: string[]
  options: string[]
  onChange: (v: string[]) => void
}

export default function BrandMultiSelect({ selected, options, onChange }: Props) {
  const { open, setOpen, ref } = useDropdown()

  function toggle(brand: string) {
    if (selected.includes(brand)) onChange(selected.filter(b => b !== brand))
    else onChange([...selected, brand])
  }

  const available = options.filter(o => !selected.includes(o))

  return (
    <div ref={ref} className="relative col-span-2 sm:col-span-1 xl:col-span-2">
      {/* chips + trigger */}
      <div
        className="input-field flex flex-wrap gap-1.5 min-h-10 cursor-pointer items-center py-1.5"
        onClick={() => setOpen((o: boolean) => !o)}
      >
        {selected.length === 0 && (
          <span className="text-gray-400 dark:text-gray-500 select-none">Brand…</span>
        )}
        {selected.map(b => (
          <span
            key={b}
            className="inline-flex items-center gap-1.5 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-sm font-medium px-2.5 py-0.5 rounded-full"
          >
            {b}
            <button
              type="button"
              onClick={e => { e.stopPropagation(); toggle(b) }}
              className="hover:text-blue-600 dark:hover:text-blue-300 leading-none text-base"
              aria-label={`Remove ${b}`}
            >
              ×
            </button>
          </span>
        ))}
        <span className="ml-auto text-gray-400 text-xs pl-1">▼</span>
      </div>

      {/* dropdown */}
      {open && available.length > 0 && (
        <div className="absolute z-50 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-56 overflow-y-auto content-scroll">
          {available.map(o => (
            <button
              key={o}
              type="button"
              onMouseDown={e => e.preventDefault()}
              onClick={() => { toggle(o); setOpen(false) }}
              className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200"
            >
              {o}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
