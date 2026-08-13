import {
  AlertTriangle,
  Download,
  ExternalLink,
  Image as ImageIcon,
  Loader2,
  RefreshCw,
  Sparkles,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { EnhanceApiError, generateImage } from '../lib/api'
import type {
  GenerateImageResponse,
  ImageAspect,
  ImageProviderChoice,
} from '../types'

type HistoryItem = {
  id: string
  image_url: string
  provider: string
  at: number
}

const HISTORY_KEY = 'aicines-image-history'
const HISTORY_MAX = 3

function loadHistory(): HistoryItem[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as HistoryItem[]
    return Array.isArray(parsed) ? parsed.slice(0, HISTORY_MAX) : []
  } catch {
    return []
  }
}

function saveHistory(items: HistoryItem[]) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(items.slice(0, HISTORY_MAX)))
  } catch {
    /* ignore quota */
  }
}

export function GeneratedImage({ prompt }: { prompt: string }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<GenerateImageResponse | null>(null)
  const [provider, setProvider] = useState<ImageProviderChoice>('auto')
  const [aspect, setAspect] = useState<ImageAspect>('portrait')
  const [imgLoaded, setImgLoaded] = useState(false)
  const [history, setHistory] = useState<HistoryItem[]>(() => loadHistory())

  const dims = useMemo(() => {
    if (aspect === 'landscape') return { width: 1024, height: 576 }
    if (aspect === 'auto') return { width: 1024, height: 1024 }
    return { width: 768, height: 1344 }
  }, [aspect])

  useEffect(() => {
    setImgLoaded(false)
  }, [result?.image_url])

  async function onGenerate() {
    if (!prompt.trim()) {
      setError('No enhanced prompt available to generate from.')
      return
    }
    setLoading(true)
    setError(null)
    setImgLoaded(false)
    try {
      const data = await generateImage({
        prompt,
        width: dims.width,
        height: dims.height,
        provider,
        aspect,
      })
      setResult(data)
      const item: HistoryItem = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        image_url: data.image_url,
        provider: data.provider,
        at: Date.now(),
      }
      setHistory((prev) => {
        const next = [item, ...prev.filter((h) => h.image_url !== item.image_url)].slice(
          0,
          HISTORY_MAX,
        )
        saveHistory(next)
        return next
      })
      if (data.provider === 'pollinations' && provider === 'gemini') {
        setError(
          'Gemini was requested but Pollinations was used. Set GEMINI_API_KEY in backend/.env and restart.',
        )
      }
    } catch (err) {
      setResult(null)
      setError(
        err instanceof EnhanceApiError
          ? err.message
          : 'Image generation failed. Please try again.',
      )
    } finally {
      setLoading(false)
    }
  }

  const showPollinationsWarning =
    provider === 'pollinations' || result?.provider === 'pollinations'

  return (
    <div className="rounded-2xl border border-stone-200 bg-white/90 p-4 shadow-sm">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-2">
          <ImageIcon className="mt-0.5 h-4 w-4 text-teal-700" />
          <div>
            <h3 className="text-sm font-semibold text-stone-800">Generated image</h3>
            <p className="mt-0.5 text-xs text-stone-500">
              Auto tries Gemini → Hugging Face → Pollinations. Pollinations needs no key.
            </p>
          </div>
        </div>
        <button
          type="button"
          disabled={loading || !prompt.trim()}
          onClick={onGenerate}
          className="inline-flex items-center gap-2 rounded-xl bg-teal-800 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Generating…
            </>
          ) : result ? (
            <>
              <RefreshCw className="h-4 w-4" />
              Regenerate
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              Generate image
            </>
          )}
        </button>
      </div>

      <div className="mb-3 flex flex-wrap gap-4">
        <ToggleGroup
          label="Provider"
          value={provider}
          onChange={setProvider}
          options={[
            { value: 'auto', label: 'Auto' },
            { value: 'huggingface', label: 'Hugging Face' },
            { value: 'gemini', label: 'Gemini' },
            { value: 'pollinations', label: 'Pollinations' },
          ]}
          disabled={loading}
        />
        <ToggleGroup
          label="Aspect"
          value={aspect}
          onChange={setAspect}
          options={[
            { value: 'portrait', label: '9:16' },
            { value: 'landscape', label: '16:9' },
            { value: 'auto', label: 'Auto' },
          ]}
          disabled={loading}
        />
      </div>

      {provider === 'gemini' && (
        <p className="mb-3 text-xs text-amber-800">
          Requires <code className="rounded bg-amber-50 px-1">GEMINI_API_KEY</code> on Render
          Environment, then redeploy
        </p>
      )}

      {provider === 'huggingface' && (
        <p className="mb-3 text-xs text-amber-800">
          Requires <code className="rounded bg-amber-50 px-1">HF_API_TOKEN</code> on{' '}
          <strong>Render → Environment</strong> (not only local .env), from{' '}
          <a
            href="https://huggingface.co/settings/tokens"
            target="_blank"
            rel="noreferrer"
            className="underline"
          >
            huggingface.co/settings/tokens
          </a>{' '}
          with Inference Providers enabled. If HF fails, the API falls back to Pollinations.
        </p>
      )}

      {showPollinationsWarning && (
        <div className="mb-3 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          Pollinations is free but lower quality. Prefer Hugging Face or Gemini when available.
        </div>
      )}

      {error && (
        <div
          role="alert"
          className="mb-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800"
        >
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-3 animate-[fadeIn_0.35s_ease]">
          <div
            className={[
              'relative overflow-hidden rounded-xl border border-stone-200 bg-stone-100',
              aspect === 'portrait' ? 'mx-auto max-w-md' : '',
            ].join(' ')}
          >
            {!imgLoaded && (
              <div className="absolute inset-0 z-10 flex min-h-[240px] flex-col items-center justify-center gap-2 bg-stone-50">
                <div className="absolute inset-0 animate-[shimmer_1.4s_linear_infinite] bg-[linear-gradient(90deg,transparent,rgba(15,118,110,0.08),transparent)] bg-[length:1000px_100%]" />
                <Loader2 className="relative h-6 w-6 animate-spin text-teal-700" />
                <span className="relative text-xs text-stone-500">Rendering pixels…</span>
              </div>
            )}
            <img
              src={result.image_url}
              alt="Generated from enhanced prompt"
              onLoad={() => setImgLoaded(true)}
              onError={() => {
                setImgLoaded(true)
                setError('Image failed to load.')
              }}
              className={[
                'mx-auto max-h-[640px] w-full object-contain transition-opacity duration-500',
                imgLoaded ? 'opacity-100' : 'opacity-0',
              ].join(' ')}
            />
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-stone-500">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-stone-200 bg-white px-3 py-1">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-teal-700" />
              Provider: <strong className="text-stone-800">{result.provider}</strong>
            </span>
            <div className="flex gap-2">
              <a
                href={result.image_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-lg border border-stone-200 bg-white px-3 py-1.5 font-medium text-teal-800 hover:border-teal-700"
              >
                <ExternalLink className="h-3.5 w-3.5" />
                Open
              </a>
              <a
                href={result.image_url}
                download="aicines-generated.png"
                className="inline-flex items-center gap-1.5 rounded-lg border border-stone-200 bg-white px-3 py-1.5 font-medium text-teal-800 hover:border-teal-700"
              >
                <Download className="h-3.5 w-3.5" />
                Download
              </a>
            </div>
          </div>
        </div>
      )}

      {history.length > 0 && (
        <div className="mt-4 border-t border-stone-200 pt-3">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-stone-500">
            Recent stills
          </p>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {history.map((h) => {
              const active = result?.image_url === h.image_url
              return (
                <button
                  key={h.id}
                  type="button"
                  onClick={() => {
                    setResult({
                      image_url: h.image_url,
                      provider: h.provider,
                      prompt_used: prompt,
                    })
                    setImgLoaded(false)
                    setError(null)
                  }}
                  className={[
                    'relative h-16 w-12 shrink-0 overflow-hidden rounded-lg border transition sm:h-20 sm:w-14',
                    active
                      ? 'border-teal-700 ring-2 ring-teal-700/30'
                      : 'border-stone-200 hover:border-teal-700/50',
                  ].join(' ')}
                  title={`From ${h.provider}`}
                >
                  <img src={h.image_url} alt="" className="h-full w-full object-cover" />
                </button>
              )
            })}
          </div>
        </div>
      )}

      {loading && <LoadingOverlay />}
    </div>
  )
}

function LoadingOverlay() {
  const phases = [
    'Interpreting prompt semantics…',
    'Composing visual structure…',
    'Diffusing latent space…',
    'Refining details…',
    'Finalizing render…',
  ]
  const [phase, setPhase] = useState(0)

  useEffect(() => {
    const id = window.setInterval(() => setPhase((p) => (p + 1) % phases.length), 1800)
    return () => window.clearInterval(id)
  }, [phases.length])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/40 backdrop-blur-sm animate-[fadeIn_0.25s_ease]">
      <div className="relative mx-4 w-full max-w-sm overflow-hidden rounded-3xl border border-stone-200 bg-[#fffdf8] p-8 text-center shadow-xl">
        <div className="pointer-events-none absolute -left-16 -top-16 h-40 w-40 rounded-full bg-teal-700/15 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-16 -right-16 h-40 w-40 rounded-full bg-amber-200/40 blur-3xl" />
        <div className="relative">
          <div className="relative mx-auto mb-6 h-20 w-20">
            <div className="absolute inset-0 rounded-full border-2 border-stone-200" />
            <div className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-teal-700 border-r-teal-500" />
            <div className="absolute inset-0 flex items-center justify-center">
              <Sparkles className="h-6 w-6 animate-pulse text-teal-700" />
            </div>
          </div>
          <h3 className="mb-2 text-lg font-semibold text-stone-900">Generating image</h3>
          <p className="mb-4 font-mono text-sm text-stone-500" key={phase}>
            {phases[phase]}
          </p>
          <div className="flex justify-center gap-1.5">
            {phases.map((_, i) => (
              <div
                key={i}
                className={[
                  'h-1.5 w-1.5 rounded-full transition-all',
                  i === phase ? 'scale-150 bg-teal-700' : 'bg-stone-300',
                ].join(' ')}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function ToggleGroup<T extends string>({
  label,
  value,
  onChange,
  options,
  disabled,
}: {
  label: string
  value: T
  onChange: (v: T) => void
  options: { value: T; label: string }[]
  disabled?: boolean
}) {
  return (
    <div>
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-stone-500">
        {label}
      </div>
      <div className="flex flex-wrap gap-1.5">
        {options.map((opt) => {
          const active = opt.value === value
          return (
            <button
              key={opt.value}
              type="button"
              disabled={disabled}
              onClick={() => onChange(opt.value)}
              className={[
                'rounded-full border px-3 py-1 text-xs font-medium transition',
                active
                  ? 'border-teal-800 bg-teal-800 text-white'
                  : 'border-stone-300 bg-white text-stone-700 hover:border-teal-700',
                disabled ? 'opacity-50' : '',
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
