import { AlertCircle, Loader2, RotateCcw, Sparkles, Wand2, Zap } from 'lucide-react'
import { useMemo, useState } from 'react'
import { ChipGroup } from './components/ChipGroup'
import { PipelineStepper } from './components/PipelineStepper'
import { ResultPanel } from './components/ResultPanel'
import { SCENE_PRESETS } from './data/presets'
import { enhancePrompt, EnhanceApiError } from './lib/api'
import { analyzeSpecificity } from './lib/specificity'
import type { EnhanceMode, EnhanceOperation, EnhanceResponse, TargetType } from './types'

const TARGETS: { value: TargetType; label: string; hint?: string }[] = [
  { value: 'general', label: 'General' },
  { value: 'image', label: 'Image' },
  { value: 'video', label: 'Video' },
  { value: 'coding', label: 'Coding' },
  { value: 'research', label: 'Research' },
]

const MODES: { value: EnhanceMode; label: string; hint: string }[] = [
  { value: 'minimal', label: 'Minimal', hint: 'Keep wording; fix clarity only' },
  { value: 'balanced', label: 'Balanced', hint: 'Default — useful specificity' },
  { value: 'advanced', label: 'Advanced', hint: 'Deeper restructure for the target' },
]

const CONTROLS: { op: EnhanceOperation; label: string }[] = [
  { op: 'more_specific', label: 'More specific' },
  { op: 'concise', label: 'Concise' },
  { op: 'creative', label: 'Creative' },
  { op: 'professional', label: 'Professional' },
  { op: 'add_constraints', label: 'Add constraints' },
  { op: 'optimize_image', label: 'Optimize image' },
  { op: 'optimize_video', label: 'Optimize video' },
  { op: 'optimize_coding', label: 'Optimize coding' },
]

export default function App() {
  const [prompt, setPrompt] = useState('')
  const [savedOriginal, setSavedOriginal] = useState('')
  const [mode, setMode] = useState<EnhanceMode>('balanced')
  const [target, setTarget] = useState<TargetType>('general')
  const [operations, setOperations] = useState<EnhanceOperation[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<EnhanceResponse | null>(null)
  const [activePreset, setActivePreset] = useState<string | null>(null)

  const canEnhance = useMemo(() => prompt.trim().length > 0 && !loading, [prompt, loading])
  const specificity = useMemo(() => analyzeSpecificity(prompt), [prompt])

  function toggleOperation(op: EnhanceOperation) {
    setOperations((prev) => (prev.includes(op) ? prev.filter((o) => o !== op) : [...prev, op]))
  }

  function applyPreset(id: string) {
    const preset = SCENE_PRESETS.find((p) => p.id === id)
    if (!preset) return
    setActivePreset(id)
    setPrompt(preset.prompt)
    setTarget(preset.target)
    setResult(null)
    setError(null)
    setSavedOriginal('')
  }

  async function runEnhance(extraOps?: EnhanceOperation[]) {
    if (!prompt.trim()) {
      setError('Enter a prompt to enhance.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      if (!savedOriginal) setSavedOriginal(prompt)
      const ops = extraOps ?? operations
      const data = await enhancePrompt({
        prompt,
        mode,
        target,
        operations: ops,
      })
      setResult(data)
    } catch (err) {
      const message =
        err instanceof EnhanceApiError
          ? err.message
          : 'Something went wrong. Please try again.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  function resetAll() {
    setPrompt(savedOriginal || '')
    setResult(null)
    setError(null)
    setMode('balanced')
    setTarget('general')
    setOperations([])
    setActivePreset(null)
  }

  function useAsInput(text: string) {
    setPrompt(text)
    setSavedOriginal('')
    setResult(null)
    setError(null)
    setActivePreset(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault()
      if (canEnhance) void runEnhance()
    }
  }

  return (
    <div className="relative min-h-screen overflow-x-hidden">
      <div className="pointer-events-none fixed inset-0 opacity-50 paper-grid" />
      <div className="pointer-events-none fixed -left-24 top-1/4 h-72 w-72 rounded-full bg-teal-700/10 blur-3xl" />
      <div className="pointer-events-none fixed -right-24 bottom-1/4 h-96 w-96 rounded-full bg-amber-200/30 blur-3xl" />

      <div className="relative z-10 mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        <header className="mb-10 max-w-2xl">
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-teal-800">
            Engineering tool
          </p>
          <h1 className="text-4xl font-semibold tracking-tight text-stone-900 sm:text-5xl">
            AI Prompt Enhancer
          </h1>
          <p className="mt-3 text-lg leading-relaxed text-stone-600">
            Turn rough ideas into clear, model-ready instructions — preserve intent, improve
            specificity.
          </p>
        </header>

        <main className="space-y-6 pb-20">
          <section className="rounded-3xl border border-stone-200 bg-[#fffdf8]/90 p-5 shadow-sm backdrop-blur-sm sm:p-7 animate-[fadeIn_0.35s_ease]">
            <div className="mb-4">
              <p className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-stone-500">
                Try a scene
              </p>
              <div className="flex flex-wrap gap-2">
                {SCENE_PRESETS.map((p) => {
                  const selected = activePreset === p.id
                  return (
                    <button
                      key={p.id}
                      type="button"
                      disabled={loading}
                      onClick={() => applyPreset(p.id)}
                      className={[
                        'rounded-full border px-3 py-1.5 text-xs font-medium transition',
                        selected
                          ? 'border-teal-700 bg-teal-700 text-white'
                          : 'border-stone-300 bg-white text-stone-700 hover:border-teal-700 hover:text-teal-800',
                        loading ? 'opacity-50' : '',
                      ].join(' ')}
                    >
                      {p.label}
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="mb-2 flex items-center justify-between gap-3">
              <label htmlFor="prompt" className="block text-sm font-semibold text-stone-800">
                Your prompt
              </label>
              <span className="font-mono text-xs text-stone-400">{prompt.length} chars</span>
            </div>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => {
                setPrompt(e.target.value)
                setActivePreset(null)
              }}
              onKeyDown={onKeyDown}
              placeholder="Enter your rough idea or prompt…"
              rows={7}
              disabled={loading}
              className="w-full resize-y rounded-2xl border border-stone-300 bg-white px-4 py-3 text-[15px] leading-relaxed text-stone-900 outline-none ring-teal-700/30 transition placeholder:text-stone-400 focus:border-teal-700 focus:ring-4 disabled:opacity-70"
            />
            <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
              <p className="text-xs text-stone-400">Tip: ⌘/Ctrl + Enter to enhance</p>
              {prompt.trim() && (
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-stone-500">Specificity</span>
                  <div className="h-1.5 w-20 overflow-hidden rounded-full bg-stone-200">
                    <div
                      className="h-full rounded-full bg-teal-700 transition-all duration-300"
                      style={{ width: `${specificity.score}%` }}
                    />
                  </div>
                  <span className="font-medium text-stone-700">{specificity.label}</span>
                </div>
              )}
            </div>

            <div className="mt-5 space-y-5">
              <ChipGroup
                label="Target"
                options={TARGETS}
                value={target}
                onChange={setTarget}
                disabled={loading}
              />
              <ChipGroup
                label="Enhancement mode"
                options={MODES}
                value={mode}
                onChange={setMode}
                disabled={loading}
              />
            </div>

            {result && (
              <div className="mt-5 border-t border-stone-200 pt-5 animate-[fadeIn_0.35s_ease]">
                <p className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-stone-500">
                  Secondary operations
                </p>
                <div className="flex flex-wrap gap-2">
                  {CONTROLS.map((c) => {
                    const selected = operations.includes(c.op)
                    return (
                      <button
                        key={c.op}
                        type="button"
                        disabled={loading}
                        onClick={() => toggleOperation(c.op)}
                        className={[
                          'inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition',
                          selected
                            ? 'border-teal-700 bg-teal-700 text-white'
                            : 'border-stone-300 bg-stone-50 text-stone-700 hover:border-teal-700 hover:text-teal-800',
                          loading ? 'opacity-50' : '',
                        ].join(' ')}
                      >
                        {selected && <Zap className="h-3 w-3" />}
                        {c.label}
                      </button>
                    )
                  })}
                </div>
                <p className="mt-2 text-xs text-stone-500">
                  Select ops, then click Enhance again to apply them together.
                </p>
              </div>
            )}

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <button
                type="button"
                disabled={!canEnhance}
                onClick={() => runEnhance()}
                className="inline-flex items-center gap-2 rounded-xl bg-stone-900 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Enhancing…
                  </>
                ) : (
                  <>
                    <Wand2 className="h-4 w-4" />
                    Enhance Prompt
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={resetAll}
                disabled={loading}
                className="inline-flex items-center gap-2 rounded-xl border border-stone-300 bg-white px-4 py-2.5 text-sm font-medium text-stone-700 transition hover:border-stone-400 disabled:opacity-50"
              >
                <RotateCcw className="h-4 w-4" />
                Reset
              </button>
            </div>

            {error && (
              <div
                role="alert"
                className="mt-5 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
              >
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}
          </section>

          <PipelineStepper active={loading} />

          {result && !loading && (
            <section className="animate-[fadeIn_0.35s_ease]">
              <div className="mb-4 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-teal-700" />
                <h2 className="text-xs font-semibold uppercase tracking-[0.14em] text-stone-500">
                  Results
                </h2>
                <div className="h-px flex-1 bg-gradient-to-r from-teal-700/30 to-transparent" />
              </div>
              <ResultPanel result={result} onUseAsInput={useAsInput} />
            </section>
          )}
        </main>

        {result && !loading && (
          <div className="fixed bottom-4 left-1/2 z-40 flex -translate-x-1/2 items-center gap-2 rounded-2xl border border-stone-200 bg-[#fffdf8]/95 px-3 py-2 shadow-lg backdrop-blur-md">
            <button
              type="button"
              onClick={() => void navigator.clipboard.writeText(result.enhanced_prompt)}
              className="rounded-xl bg-stone-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-teal-800"
            >
              Copy enhanced
            </button>
            <button
              type="button"
              onClick={() => useAsInput(result.enhanced_prompt)}
              className="rounded-xl border border-stone-300 bg-white px-3 py-1.5 text-xs font-medium text-stone-700 hover:border-teal-700"
            >
              Use as input
            </button>
            <button
              type="button"
              onClick={() => runEnhance()}
              className="rounded-xl border border-stone-300 bg-white px-3 py-1.5 text-xs font-medium text-stone-700 hover:border-teal-700"
            >
              Re-enhance
            </button>
          </div>
        )}

        <footer className="mt-12 border-t border-stone-200 pt-6 text-center text-xs text-stone-500">
          AICines · Prompt Enhancer — preserve intent, improve specificity. Quality is a rubric score,
          not length.
        </footer>
      </div>
    </div>
  )
}
