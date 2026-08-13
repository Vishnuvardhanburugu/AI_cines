interface Option<T extends string> {
  value: T
  label: string
  hint?: string
}

interface ChipGroupProps<T extends string> {
  label: string
  options: Option<T>[]
  value: T
  onChange: (value: T) => void
  disabled?: boolean
}

export function ChipGroup<T extends string>({
  label,
  options,
  value,
  onChange,
  disabled,
}: ChipGroupProps<T>) {
  return (
    <div className="space-y-2">
      <div className="text-xs font-semibold uppercase tracking-[0.14em] text-stone-500">
        {label}
      </div>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => {
          const active = opt.value === value
          return (
            <button
              key={opt.value}
              type="button"
              disabled={disabled}
              title={opt.hint}
              onClick={() => onChange(opt.value)}
              className={[
                'rounded-full border px-3.5 py-1.5 text-sm transition',
                active
                  ? 'border-teal-700 bg-teal-700 text-white shadow-sm'
                  : 'border-stone-300 bg-white/70 text-stone-700 hover:border-teal-600 hover:text-teal-800',
                disabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer',
              ].join(' ')}
            >
              {opt.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
