# Deployment Guide — Free-Tier Hosting

This app is two separately-deployed pieces: a Next.js frontend and a
FastAPI backend. The backend is the constraint that matters most when
picking a host — both OCR and Speech-to-Text depend on **WebSockets**
(`WS /api/v1/ocr/live`, `WS /api/v1/speech/live`) for live progress and
live transcription, which rules out pure serverless-function platforms
(classic Vercel/Netlify serverless functions cannot hold a long-lived
socket open). The frontend has no such constraint — it's a standard
Next.js app.

## Recommended combination (both genuinely free, no credit card)

| Piece | Platform | Why |
|---|---|---|
| Frontend | **Vercel** (Hobby/Free tier) | Built by the Next.js authors — zero-config deploy straight from GitHub, generous free bandwidth/build minutes, no card required |
| Backend | **Render** (Free Web Service) | Runs a real persistent process (not serverless), full WebSocket support, no card required. Trade-off: spins down after 15 minutes of no traffic and takes ~30–50s to wake back up on the next request — fine for a portfolio/demo, not for guaranteed always-on |

## Alternatives if you want always-on (require a card for identity verification, but stay within the free allowance)

| Platform | Free allowance | Notes |
|---|---|---|
| **Fly.io** | 3 shared-cpu-1x 256MB VMs | True always-on, full WebSocket support, deploys straight from your `backend/Dockerfile`. Card required for verification but the free allowance itself isn't charged |
| **Google Cloud Run** | 2M requests/month, 360k GB-seconds | WebSockets work but need `--session-affinity` enabled; most generous free tier by far, but the most setup (gcloud CLI + Docker) |
| **Koyeb** | 1 free "nano" web service | No card required, supports WebSockets, but very limited CPU/RAM — expect it to feel slow under any real load |

Railway is deliberately left off this list — it removed its indefinite free tier and now only gives a one-time trial credit, not a repeatable free plan.

---

## Deploying the backend on Render (recommended path)

1. Go to [render.com](https://render.com) → sign up with your GitHub account (no card needed).
2. **New** → **Web Service** → connect the `OCR-STT-NEXTUPGRAD-mistral.ai-` repo.
3. Configure:
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -e ".[dev]"` (or just `pip install .` — dev deps aren't needed in production)
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free
4. Add environment variables (Render dashboard → Environment):

   | Key | Value |
   |---|---|
   | `ENVIRONMENT` | `production` |
   | `MISTRAL_API_KEY` | *your real Mistral API key* |
   | `MISTRAL_BASE_URL` | `https://api.mistral.ai` |
   | `OCR_MODEL` | `mistral-ocr-latest` |
   | `STT_MODEL` | `voxtral-mini-latest` |
   | `STT_REALTIME_MODEL` | `voxtral-mini-transcribe-realtime-2602` |
   | `STT_STREAMING_DELAY_MS` | `250` |
   | `STT_REFINE_AFTER_STOP` | `true` |
   | `CORS_ORIGINS` | *your Vercel URL, e.g.* `https://your-app.vercel.app` |
   | `MAX_UPLOAD_SIZE_MB` | `100` |
   | `OCR_TIMEOUT_SECONDS` | `30` |
   | `OCR_BATCH_PAGES` | `20` |
   | `OCR_MAX_PAGES` | `1500` |
   | `OCR_SECONDS_PER_PAGE` | `15` |
   | `OCR_BATCH_TIMEOUT_FLOOR_SECONDS` | `60` |
   | `SPEECH_TIMEOUT_SECONDS` | `60` |
   | `RATE_LIMIT_REQUESTS_PER_MINUTE` | `10` |

5. Deploy. Render gives you a URL like `https://ocr-stt-backend.onrender.com` — that's your backend's public address. Confirm it's alive by opening `https://ocr-stt-backend.onrender.com/api/v1/health`.

**Important**: `ENVIRONMENT=production` switches CORS from the permissive localhost regex to the explicit `CORS_ORIGINS` allowlist — so `CORS_ORIGINS` must exactly match your deployed frontend's origin (scheme + host, no trailing slash), or every request will be rejected by the browser.

## Deploying the frontend on Vercel

1. Go to [vercel.com](https://vercel.com) → sign up with GitHub.
2. **Add New** → **Project** → import the same repo.
3. Configure:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Next.js (auto-detected)
   - Build/output settings: leave as default (`next build`, `.next`)
4. Add one environment variable:

   | Key | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | *your Render backend URL, e.g.* `https://ocr-stt-backend.onrender.com` |

   The frontend derives its WebSocket URL from this same variable
   (`http`→`ws`, `https`→`wss`, see [`frontend/lib/api.ts`](../frontend/lib/api.ts)) —
   you only ever set this one value, never a separate WS URL.

5. Deploy. Vercel gives you a URL like `https://your-app.vercel.app`.
6. **Go back to Render** and set `CORS_ORIGINS` to this exact Vercel URL, then redeploy the backend so CORS actually allows it.

## What you need in hand before starting

- A [Mistral AI API key](https://console.mistral.ai/) (paste as `MISTRAL_API_KEY` on the backend — never on the frontend, never in a public repo).
- A GitHub account with this repo pushed (already done).
- A Render account (free, no card) and a Vercel account (free, no card).
- 10–15 minutes — most of it is waiting for the first build.

## Known trade-offs of the free path

- **Cold starts**: Render's free tier sleeps the backend after 15 minutes of no traffic. The first OCR/Speech request after a sleep will hang for 30–50 seconds while it wakes up — this is Render's limitation, not an app bug. If you need always-on for a demo, use Fly.io instead (see the alternatives table).
- **Rate limiter resets on restart**: the in-memory sliding-window limiter (`RATE_LIMIT_REQUESTS_PER_MINUTE`) lives in process memory, so a Render cold-start (or a Fly.io redeploy) clears it. Expected and harmless for this app's scale.
- **No persistent storage**: there's no database in this app by design (see [Explicit non-goals](prd/01-foundation.md#non-goals)), so nothing is lost across a restart that wasn't already lost by design.

---
**Author:** Pranjul Rathour
**Designation:** GenAI Engineer
**Organization:** NEXT UPGRAD WEB SOLUTIONS
