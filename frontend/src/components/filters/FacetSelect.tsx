import { useDropdown } from '../../hooks/useDropdown'

interface Props {
  placeholder: string
  value: string
  options: string[]
  onChange: (v: string) => void
}

export default function FacetSelect({ placeholder, value, options, onChange }: Props) {
  const { open, setOpen, ref } = useDropdown()

  return (
    <div ref={ref} className="relative">
      {/* trigger */}
      <div
        onClick={() => setOpen((o: boolean) => !o)}
        className="input-field flex items-center cursor-pointer select-none pr-8"
      >
        <span className={value ? 'text-gray-900 dark:text-gray-100' : 'text-gray-400 dark:text-gray-500'}>
          {value || placeholder}
        </span>
        {value && (
          <button
            type="button"
            onMouseDown={e => e.stopPropagation()}
            onClick={e => { e.stopPropagation(); onChange(''); setOpen(false) }}
            className="absolute right-7 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 leading-none"
            aria-label="Clear"
          >
            ✕
          </button>
        )}
        <span className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-xs">▼</span>
      </div>

      {/* dropdown */}
      {open && (
        <div className="absolute z-50 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-56 overflow-y-auto content-scroll">
          {options.map(o => (
            <button
              key={o}
              type="button"
              onMouseDown={e => e.preventDefault()}
              onClick={() => { onChange(o); setOpen(false) }}
              className={`w-full text-left px-3 py-2 text-sm transition-colors ${
                o === value
                  ? 'bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 font-medium'
                  : 'hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200'
              }`}
            >
              {o}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
