interface QualityBarProps {
  before: number
  after: number
  changes?: string[]
}

export function QualityBar({ before, after, changes }: QualityBarProps) {
  const delta = after - before
  return (
    <div>
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <h3 className="text-sm font-semibold text-stone-800">Prompt quality</h3>
        <span className="text-xs text-stone-500">Rubric score (not length)</span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <ScoreRow label="Before" value={before} tone="muted" />
        <ScoreRow label="After" value={after} tone="accent" />
      </div>
      <p className="mt-3 text-sm text-stone-600">
        {delta > 0
          ? `+${delta} points — more complete and specific for the task.`
          : delta === 0
            ? 'Score unchanged — original was already fairly complete.'
            : `${delta} points — enhancement was constrained to preserve intent.`}
      </p>
      {changes && changes.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {changes.slice(0, 4).map((c) => (
            <span
              key={c}
              className="rounded-full border border-teal-700/20 bg-teal-50 px-2 py-0.5 text-[11px] font-medium text-teal-900"
            >
              {c.length > 42 ? `${c.slice(0, 40)}…` : c}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function ScoreRow({
  label,
  value,
  tone,
}: {
  label: string
  value: number
  tone: 'muted' | 'accent'
}) {
  const clamped = Math.max(0, Math.min(100, value))
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-stone-500">
        <span>{label}</span>
        <span className="font-medium text-stone-800">{clamped}/100</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-stone-200">
        <div
          className={
            tone === 'accent'
              ? 'h-full rounded-full bg-teal-700 transition-all duration-500'
              : 'h-full rounded-full bg-stone-400 transition-all duration-500'
          }
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  )
}
