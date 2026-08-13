/** Lightweight word diff: tokens in `next` that aren't in `prev` are "added". */

export type DiffToken = { text: string; added: boolean }

export function tokenize(text: string): string[] {
  return text.split(/(\s+)/).filter((t) => t.length > 0)
}

export function diffWords(prev: string, next: string): DiffToken[] {
  const prevSet = new Set(
    tokenize(prev)
      .map((t) => t.trim().toLowerCase())
      .filter(Boolean),
  )
  return tokenize(next).map((text) => {
    const key = text.trim().toLowerCase()
    if (!key || /^\s+$/.test(text)) return { text, added: false }
    return { text, added: !prevSet.has(key) }
  })
}
