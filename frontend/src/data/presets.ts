import type { TargetType } from '../types'

export type ScenePreset = {
  id: string
  label: string
  target: TargetType
  prompt: string
}

export const SCENE_PRESETS: ScenePreset[] = [
  {
    id: 'mythic',
    label: 'Mythic epic',
    target: 'image',
    prompt:
      'Hanuman standing on a cliff overlooking burning Lanka at night, epic cinematic still',
  },
  {
    id: 'scifi',
    label: 'Sci-fi city',
    target: 'video',
    prompt:
      'Neon rain on a futuristic megacity street at night, camera tracking a courier bike through traffic',
  },
  {
    id: 'product',
    label: 'Product shot',
    target: 'image',
    prompt: 'Matte black wireless earbuds on white marble, soft studio light, clean commercial photo',
  },
  {
    id: 'coding',
    label: 'Coding task',
    target: 'coding',
    prompt: 'Write a Python FastAPI endpoint that uploads an image and returns YOLO detections as JSON',
  },
  {
    id: 'research',
    label: 'Research brief',
    target: 'research',
    prompt: 'Summarize recent approaches to RAG evaluation and list tradeoffs for production chatbots',
  },
]
