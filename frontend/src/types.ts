export type EnhanceMode = 'minimal' | 'balanced' | 'advanced'

export type TargetType =
  | 'general'
  | 'image'
  | 'video'
  | 'coding'
  | 'research'
  | 'chatgpt'
  | 'claude'
  | 'gemini'
  | 'custom'

export type EnhanceOperation =
  | 'more_specific'
  | 'concise'
  | 'creative'
  | 'professional'
  | 'add_constraints'
  | 'optimize_image'
  | 'optimize_video'
  | 'optimize_coding'

export interface EnhanceRequest {
  prompt: string
  mode: EnhanceMode
  target: TargetType
  operations?: EnhanceOperation[]
}

export interface EnhanceResponse {
  original_prompt: string
  enhanced_prompt: string
  structured_prompt?: string | null
  category: string
  quality_before: number
  quality_after: number
  changes: string[]
  assumptions: string[]
  explanation: string
  clarification_questions: string[]
  analysis?: string | null
}

export interface ApiError {
  detail: string
}

export type ImageProviderChoice = 'auto' | 'gemini' | 'pollinations'
export type ImageAspect = 'auto' | 'portrait' | 'landscape'

export interface GenerateImageRequest {
  prompt: string
  width?: number
  height?: number
  provider?: ImageProviderChoice
  aspect?: ImageAspect
}

export interface GenerateImageResponse {
  image_url: string
  provider: string
  prompt_used: string
}
