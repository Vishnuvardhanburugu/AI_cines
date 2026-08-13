/** Lightweight client-side specificity hints (not the backend rubric). */

const SIGNALS: { id: string; label: string; patterns: RegExp[] }[] = [
  { id: 'subject', label: 'Subject', patterns: [/\b(hanuman|rama|city|dog|person|character|product)\b/i, /\bof a\b/i] },
  { id: 'action', label: 'Action', patterns: [/\b(running|burning|flying|create|write|build|detect|standing|racing)\b/i] },
  { id: 'setting', label: 'Setting', patterns: [/\b(city|park|room|lanka|forest|street|night|day|harbor|cliff)\b/i] },
  { id: 'camera', label: 'Camera', patterns: [/\b(camera|tracking|shot|lens|drone|close-up|wide|tilt|pan|angle)\b/i] },
  { id: 'lighting', label: 'Lighting', patterns: [/\b(lighting|neon|moonlight|firelight|volumetric|sunlight|rim light)\b/i] },
  { id: 'style', label: 'Style', patterns: [/\b(cinematic|photoreal|realistic|style|anime|cartoon)\b/i] },
  { id: 'constraints', label: 'Constraints', patterns: [/\b(no |avoid|must|should|without|do not|don't)\b/i] },
  { id: 'output', label: 'Output', patterns: [/\b(format|json|email|markdown|response|return|still|video)\b/i] },
]

export function analyzeSpecificity(prompt: string): {
  score: number
  label: string
  present: string[]
  missing: string[]
} {
  const present: string[] = []
  const missing: string[] = []
  for (const s of SIGNALS) {
    if (s.patterns.some((p) => p.test(prompt))) present.push(s.label)
    else missing.push(s.label)
  }
  const score = Math.round((present.length / SIGNALS.length) * 100)
  let label = 'Weak'
  if (score >= 75) label = 'Strong'
  else if (score >= 45) label = 'Okay'
  else if (score >= 25) label = 'Thin'
  return { score, label, present, missing }
}
