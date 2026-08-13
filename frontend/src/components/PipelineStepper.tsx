import { Check, Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'

const STEPS = [
  { id: 'analyze', label: 'Analyze' },
  { id: 'enhance', label: 'Enhance' },
  { id: 'validate', label: 'Validate' },
] as const

/** Visual pipeline while enhance is in flight (client-timed; mirrors backend stages). */
export function PipelineStepper({ active }: { active: boolean }) {
  const [step, setStep] = useState(0)

  useEffect(() => {
    if (!active) {
      setStep(0)
      return
    }
    setStep(0)
    const t1 = window.setTimeout(() => setStep(1), 700)
    const t2 = window.setTimeout(() => setStep(2), 1600)
    return () => {
      window.clearTimeout(t1)
      window.clearTimeout(t2)
    }
  }, [active])

  if (!active) return null

  return (
    <div className="rounded-2xl border border-stone-200 bg-white/80 px-4 py-5 shadow-sm animate-[fadeIn_0.3s_ease]">
      <p className="mb-4 text-center text-xs font-semibold uppercase tracking-[0.14em] text-stone-500">
        Enhancement pipeline
      </p>
      <div className="flex items-center justify-center gap-2 sm:gap-4">
        {STEPS.map((s, i) => {
          const done = i < step
          const current = i === step
          return (
            <div key={s.id} className="flex items-center gap-2 sm:gap-4">
              <div className="flex flex-col items-center gap-1.5">
                <div
                  className={[
                    'flex h-9 w-9 items-center justify-center rounded-full border text-sm transition',
                    done
                      ? 'border-teal-700 bg-teal-700 text-white'
                      : current
                        ? 'border-teal-700 bg-teal-50 text-teal-800'
                        : 'border-stone-200 bg-stone-50 text-stone-400',
                  ].join(' ')}
                >
                  {done ? (
                    <Check className="h-4 w-4" />
                  ) : current ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    i + 1
                  )}
                </div>
                <span
                  className={[
                    'text-xs font-medium',
                    done || current ? 'text-stone-800' : 'text-stone-400',
                  ].join(' ')}
                >
                  {s.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div
                  className={[
                    'mb-5 h-px w-8 sm:w-14 transition',
                    done ? 'bg-teal-700' : 'bg-stone-200',
                  ].join(' ')}
                />
              )}
            </div>
          )
        })}
      </div>
      <p className="mt-4 text-center text-sm text-stone-500">
        {step === 0 && 'Extracting intent and material gaps…'}
        {step === 1 && 'Building a more specific master prompt…'}
        {step === 2 && 'Checking intent preservation…'}
      </p>
    </div>
  )
}
