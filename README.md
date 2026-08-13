# Semantic AI Prompt Enhancer

Turn rough ideas into clear, model-ready instructions while **preserving intent** and improving **specificity** — not vocabulary.

## Architecture

```
USER INPUT → Analyze → Enhance → Validate (+ retry / degrade) → Response
```

- **Analyze**: classify, extract intent, detect material gaps
- **Enhance**: category- and mode-aware rewrite with listed assumptions
- **Validate**: deterministic guards + LLM check; regenerate once, then degrade to minimal

Quality scores use a **deterministic rubric** (clarity, specificity, completeness, constraints, output definition) — not prompt length.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Vite, React, TypeScript, Tailwind |
| Backend | FastAPI, Pydantic v2 |
| LLM | Provider interface — **Gemini (default)**, Grok/xAI, OpenAI, Anthropic, local, mock |

API keys stay on the backend only.

### Free keys — quick truth

- **Gemini:** Free developer API via [Google AI Studio](https://aistudio.google.com/apikey) (rate-limited Flash models). Recommended default.
- **Grok:** Free chat on X/grok.com ≠ free API. xAI API is generally paid/prepaid. Optional via `XAI_API_KEY`.
- **Mock:** `LLM_PROVIDER=mock` uses an offline cinematic composer (no key). Good for demos.
- **Images:** After enhance, click **Generate image**. For **Gemini-quality** mythic/epic stills (portrait 9:16), set `GEMINI_API_KEY` and choose Provider **Gemini** in the UI. Without a key, [Pollinations](https://image.pollinations.ai) is used (free, lower quality). **Video generation is not included**.

## Quick start (local)

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
# Set GEMINI_API_KEY, or use LLM_PROVIDER=mock for offline cinematic demos
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — Vite proxies `/api` to the backend.

### Mock mode (no API key)

```bash
LLM_PROVIDER=mock uvicorn app.main:app --reload --port 8000
```

### Gemini (recommended free)

```bash
# in backend/.env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
```

## API

`POST /api/enhance`

```json
{
  "prompt": "Make a video of a futuristic city.",
  "mode": "balanced",
  "target": "video",
  "operations": []
}
```

Response includes:
- `enhanced_prompt` — flowing cinematic paragraph (ready to paste)
- `structured_prompt` — labeled master sections (Subject / Camera / Lighting / …) for video/image
- `category`, `quality_before` / `quality_after`, `changes`, `assumptions`, `explanation`, `clarification_questions`

Internal chain-of-thought is never exposed.

`POST /api/generate-image`

```json
{
  "prompt": "Create a photoreal cinematic still of …",
  "width": 1024,
  "height": 576
}
```

Returns `{ "image_url", "provider", "prompt_used" }`. Free via Pollinations (URL) or optional Gemini (data URL).

## Modes

- **Minimal** — keep wording; clarity only
- **Balanced** — default useful specificity
- **Advanced** — deeper restructure for the target pack

## Targets

`general`, `image`, `video`, `coding`, `research`, plus light structural packs for `chatgpt` / `claude` / `gemini` (not claimed as proprietary “optimization”).

## Tests

```bash
cd backend
LLM_PROVIDER=mock pytest -q
```

Evaluation dataset: `backend/app/evaluation/dataset.json` (includes the three specification examples).

## Docker

**Local (two services):**

```bash
cp .env.example .env
# set GEMINI_API_KEY or LLM_PROVIDER=mock
docker compose up --build
```

Frontend: http://localhost:3000 · Backend: http://localhost:8000

**Single image (Render / PaaS expecting root `Dockerfile`):**

```bash
docker build -t aicines .
docker run --rm -p 8000:8000 -e PORT=8000 -e LLM_PROVIDER=mock aicines
```

Open http://localhost:8000 — SPA + `/api` on one port. On Render, set env vars (`GEMINI_API_KEY`, `LLM_PROVIDER`, etc.) in the dashboard; Dockerfile path can stay `./Dockerfile`.

## Design principles

1. Preserve intent; improve specificity
2. Do not invent frameworks, dates, or storylines silently
3. List creative assumptions
4. Prefer material gaps over padding
5. Keep the prompt the center of the UI
