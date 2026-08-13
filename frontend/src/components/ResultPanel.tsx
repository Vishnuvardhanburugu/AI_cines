import { ArrowUpToLine, FileText, HelpCircle, Lightbulb, ListChecks } from 'lucide-react'
import type { EnhanceResponse } from '../types'
import { CopyButton } from './CopyButton'
import { GeneratedImage } from './GeneratedImage'
import { PromptDiff } from './PromptDiff'
import { QualityBar } from './QualityBar'

function parseStructured(structured: string): { label: string; body: string }[] {
  const lines = structured.split('\n').map((l) => l.trim()).filter(Boolean)
  const out: { label: string; body: string }[] = []
  for (const line of lines) {
    const m = line.match(/^([^:]+):\s*(.*)$/)
    if (m) out.push({ label: m[1].trim(), body: m[2].trim() })
  }
  return out
}

export function ResultPanel({
  result,
  onUseAsInput,
}: {
  result: EnhanceResponse
  onUseAsInput?: (text: string) => void
}) {
  const structuredSections = result.structured_prompt
    ? parseStructured(result.structured_prompt)
    : []

  return (
    <section className="space-y-5">
      <div className="grid gap-4 lg:grid-cols-2">
        <PromptCard title="Original prompt" text={result.original_prompt} muted />
        <div className="space-y-3">
          <PromptCard
            title="Cinematic paragraph (ready to paste)"
            text={result.enhanced_prompt}
            emphasize
            onUseAsInput={onUseAsInput}
          />
        </div>
      </div>

      <PromptDiff original={result.original_prompt} enhanced={result.enhanced_prompt} />

      {structuredSections.length > 0 && (
        <div className="rounded-2xl border border-stone-200 bg-white/90 p-4 shadow-sm sm:p-5 animate-[fadeIn_0.35s_ease]">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-teal-700" />
              <h3 className="text-sm font-semibold text-stone-800">Structured master prompt</h3>
            </div>
            <CopyButton text={result.structured_prompt || ''} label="Copy all" />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {structuredSections.map((s) => (
              <div
                key={s.label}
                className="rounded-xl border border-stone-200 bg-stone-50/80 p-3.5 transition hover:border-teal-700/40"
              >
                <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-teal-800">
                  {s.label}
                </p>
                <p className="text-sm leading-relaxed text-stone-700">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {result.structured_prompt && structuredSections.length === 0 && (
        <PromptCard
          title="Structured master prompt"
          text={result.structured_prompt}
          emphasize
        />
      )}

      <div className="grid gap-4 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <GeneratedImage prompt={result.enhanced_prompt} />
        </div>
        <div className="space-y-4 lg:col-span-2">
          <div className="rounded-2xl border border-stone-200 bg-white/90 p-4 shadow-sm">
            <QualityBar
              before={result.quality_before}
              after={result.quality_after}
              changes={result.changes}
            />
            <div className="mt-4 border-t border-stone-200 pt-3 text-xs text-stone-500">
              Category:{' '}
              <strong className="rounded-full border border-stone-200 bg-stone-50 px-2 py-0.5 text-stone-800">
                {result.category}
              </strong>
            </div>
          </div>
          {result.explanation && (
            <InfoCard
              icon={<Lightbulb className="h-4 w-4 text-teal-700" />}
              title="Explanation"
              tone="teal"
            >
              {result.explanation}
            </InfoCard>
          )}
        </div>
      </div>

      {result.analysis && (
        <InfoCard icon={<HelpCircle className="h-4 w-4 text-stone-500" />} title="Analysis">
          {result.analysis}
        </InfoCard>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <ListCard
          icon={<ListChecks className="h-4 w-4 text-teal-700" />}
          title="What changed"
          items={result.changes}
          empty="No structural changes reported."
        />
        <ListCard
          icon={<AlertDot />}
          title="Assumptions"
          items={result.assumptions}
          empty="No creative assumptions were added."
          warn
        />
      </div>

      {result.clarification_questions?.length > 0 && (
        <ListCard
          icon={<HelpCircle className="h-4 w-4 text-stone-500" />}
          title="Optional clarifications"
          items={result.clarification_questions}
          empty=""
        />
      )}
    </section>
  )
}

function AlertDot() {
  return <span className="mt-0.5 inline-block h-2.5 w-2.5 rounded-full bg-amber-600" />
}

function PromptCard({
  title,
  text,
  muted,
  emphasize,
  onUseAsInput,
}: {
  title: string
  text: string
  muted?: boolean
  emphasize?: boolean
  onUseAsInput?: (text: string) => void
}) {
  return (
    <div
      className={[
        'rounded-2xl border p-4 shadow-sm',
        emphasize
          ? 'border-teal-700/30 bg-white'
          : muted
            ? 'border-stone-200 bg-stone-50/80'
            : 'border-stone-200 bg-white',
      ].join(' ')}
    >
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-stone-800">{title}</h3>
        <div className="flex flex-wrap items-center gap-2">
          {onUseAsInput && (
            <button
              type="button"
              onClick={() => onUseAsInput(text)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-stone-200 bg-white px-2.5 py-1 text-xs font-medium text-stone-700 transition hover:border-teal-700 hover:text-teal-800"
            >
              <ArrowUpToLine className="h-3.5 w-3.5" />
              Use as input
            </button>
          )}
          <CopyButton text={text} />
        </div>
      </div>
      <pre className="whitespace-pre-wrap font-sans text-[15px] leading-relaxed text-stone-800">
        {text}
      </pre>
    </div>
  )
}

function InfoCard({
  icon,
  title,
  children,
  tone,
}: {
  icon: React.ReactNode
  title: string
  children: React.ReactNode
  tone?: 'teal'
}) {
  return (
    <div
      className={[
        'rounded-2xl border p-4 text-sm leading-relaxed text-stone-800',
        tone === 'teal'
          ? 'border-stone-200 bg-teal-50/60'
          : 'border-stone-200 bg-white/80',
      ].join(' ')}
    >
      <div className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-stone-500">
        {icon}
        {title}
      </div>
      {children}
    </div>
  )
}

function ListCard({
  title,
  items,
  empty,
  warn,
  icon,
}: {
  title: string
  items: string[]
  empty: string
  warn?: boolean
  icon?: React.ReactNode
}) {
  return (
    <div className="rounded-2xl border border-stone-200 bg-white/80 p-4">
      <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-stone-800">
        {icon}
        {title}
      </h3>
      {items?.length ? (
        <ul className="space-y-1.5 text-sm text-stone-700">
          {items.map((item) => (
            <li key={item} className="flex gap-2">
              <span className={warn ? 'text-amber-700' : 'text-teal-700'}>•</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-stone-500">{empty}</p>
      )}
    </div>
  )
}
