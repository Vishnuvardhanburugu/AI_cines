import type {
  EnhanceRequest,
  EnhanceResponse,
  GenerateImageRequest,
  GenerateImageResponse,
} from '../types'

const API_BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? ''

export class EnhanceApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'EnhanceApiError'
    this.status = status
  }
}

async function postJson<T>(path: string, body: unknown, timeoutMs = 90000): Promise<T> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs)

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    })

    let data: unknown
    try {
      data = await res.json()
    } catch {
      throw new EnhanceApiError('Received an unreadable response from the server.', res.status)
    }

    if (!res.ok) {
      const detail =
        typeof data === 'object' &&
        data !== null &&
        'detail' in data &&
        typeof (data as { detail: unknown }).detail === 'string'
          ? (data as { detail: string }).detail
          : Array.isArray((data as { detail?: unknown }).detail)
            ? 'Invalid request. Check your inputs and try again.'
            : 'Request failed. Please try again.'
      throw new EnhanceApiError(detail, res.status)
    }

    return data as T
  } catch (err) {
    if (err instanceof EnhanceApiError) throw err
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new EnhanceApiError('The request timed out. Please try again.', 504)
    }
    throw new EnhanceApiError(
      'Could not reach the enhancement service. Is the backend running?',
      0,
    )
  } finally {
    window.clearTimeout(timeout)
  }
}

export async function enhancePrompt(body: EnhanceRequest): Promise<EnhanceResponse> {
  return postJson<EnhanceResponse>('/api/enhance', body, 90000)
}

export async function generateImage(
  body: GenerateImageRequest,
): Promise<GenerateImageResponse> {
  return postJson<GenerateImageResponse>('/api/generate-image', body, 120000)
}
