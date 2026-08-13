import { diffWords } from '../lib/diff'
import { CopyButton } from './CopyButton'

export function PromptDiff({
  original,
  enhanced,
}: {
  original: string
  enhanced: string
}) {
  const tokens = diffWords(original, enhanced)
  const addedCount = tokens.filter((t) => t.added).length

  return (
    <div className="rounded-2xl border border-teal-700/25 bg-white p-4 shadow-sm">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-stone-800">What was added</h3>
          <p className="text-xs text-stone-500">
            Green highlights are new specificity vs your original ({addedCount} new tokens)
          </p>
        </div>
        <CopyButton text={enhanced} />
      </div>
      <pre className="whitespace-pre-wrap font-sans text-[15px] leading-relaxed text-stone-800">
        {tokens.map((t, i) =>
          t.added ? (
            <mark
              key={i}
              className="rounded-sm bg-teal-100 px-0.5 text-teal-950 decoration-transparent"
            >
              {t.text}
            </mark>
          ) : (
            <span key={i}>{t.text}</span>
          ),
        )}
      </pre>
    </div>
  )
}
