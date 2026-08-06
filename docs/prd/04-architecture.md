# Part 4 — Frontend Architecture, Backend Architecture, Folder Structure & Performance Engineering

## 41. Architecture Philosophy

Engineer like production SaaS, not a proof-of-concept: scalability,
maintainability, performance, separation of concerns, low coupling, high
cohesion, reusability, type safety. Every module should be replaceable
without affecting other modules.

## 42. High-Level System Architecture

```
User → Next.js Frontend → (OCR Module | Speech Module) → API Service Layer
     → FastAPI Backend → (Mistral OCR API | Mistral Voxtral API)
```

**The frontend must never communicate directly with Mistral.** All calls go
through FastAPI.

## 43. Frontend Stack

Next.js 15 (App Router) · TypeScript · Tailwind CSS v4 · shadcn/ui · Lucide
React · Framer Motion · React Hook Form · Zod · Sonner.

## 44. Backend Stack

FastAPI · Uvicorn (ASGI) · Pydantic · httpx · python-dotenv. Future-ready for
WebSockets (already required for live speech streaming).

## 45. Frontend Folder Structure

```
frontend/
  app/
    layout.tsx
    page.tsx
    globals.css
  components/
    common/
    layout/
    ocr/
    speech/
    ui/
  features/
    ocr/
    speech/
  hooks/
    useOCR.ts
    useSpeech.ts
    useTheme.ts
  lib/
    api.ts
    constants.ts
    utils.ts
  services/
    ocr.service.ts
    speech.service.ts
  types/
    api.ts
    ocr.ts
    speech.ts
  styles/
  public/
  assets/
```

Every folder has a single responsibility.

## 46. Backend Folder Structure

```
backend/
  app/
    api/
      ocr.py
      speech.py
    core/
      config.py
    schemas/
      ocr.py
      speech.py
    services/
      mistral_ocr.py
      mistral_speech.py
    utils/
  main.py
```

(Part 5 refines this further with `middleware/`, `schemas/request.py` /
`response.py`, and `health.py` — see [05-api-spec.md §74](05-api-spec.md).
Part 5's structure is the one actually implemented; this section is the
initial sketch.)

No business logic inside API routes — routes call services only.

## 47. Component Hierarchy

```
App → Navbar → Page → Feature → Card → Reusable Components → UI Elements
```

Example: `SpeechPage → SpeechCard → TranscriptCard → CopyButton`

## 48. Component Rules

Every component must be reusable, typed, accept props, never duplicate code,
and use composition over inheritance. Avoid giant components — max
250–300 lines; split when exceeded.

## 49. State Management

| Need | Tool |
|---|---|
| Local state | `useState` |
| Shared state | Context API |
| Derived state | `useMemo` |
| Expensive calculations | `useMemo` |
| Stable callbacks | `useCallback` |
| DOM access | `useRef` |

Avoid unnecessary global state — no Redux/Zustand unless a real cross-cutting
need emerges.

## 50. API Layer

Never call `fetch` directly inside components.

```
Wrong:   Component → fetch()
Correct: Component → Service → API Client → Backend
```

## 51. API Structure

`lib/api.ts` → `services/*` → hooks → components. This separates UI from
networking.

## 52. Data Flow

**OCR:** Upload → Validation → API Service → FastAPI → Mistral OCR →
Formatted Response → UI

**Speech:** Mic → Recorder → API Service → FastAPI → Voxtral → Streaming →
Transcript

## 53. Environment Variables

**Frontend:** `NEXT_PUBLIC_API_URL`

**Backend:** `MISTRAL_API_KEY`, `PORT`, `HOST`

Never expose API keys to the frontend.

## 54. Error Boundary

App-wide React Error Boundary. On crash, show "Something went wrong." +
Retry — never a white screen.

## 55–56. Performance Philosophy & Frontend Performance Rules

Performance is a feature — optimize CPU, memory, network, rendering.

**Use:** lazy loading, dynamic imports, code splitting, memoization, image
optimization, tree shaking, font optimization, streaming UI.

**Avoid:** large libraries, unused CSS, large bundles, duplicate
dependencies, blocking rendering.

## 57. Rendering Strategy

Prefer Server Components. Use Client Components only where required:
ThemeToggle, Speech Recorder, OCR Upload. Everything else stays server.

## 58. API Performance

Compression, connection reuse, timeout handling, retries, caching where
possible, `AbortController` support, no duplicate requests.

## 59. File Upload Optimization

Validate → compress if needed → show preview → allow cancel/retry. Max file
size configurable via settings, not hardcoded.

## 60. Speech Performance

Recording starts instantly, low latency, smooth transcript updates, no UI
freezes, no dropped frames. Recording must continue even if the UI rerenders.

## 61. Memory Management

Always cleanup: event listeners, timers, microphone streams; abort in-flight
API requests on unmount; release blobs after download. Prevent leaks.

## 62. Caching Strategy

Cache: theme, user preferences, static assets, fonts, icons. Do **not** cache
transcripts or OCR results unless explicitly added later.

## 63. Network Strategy

Show offline state, detect slow network, retry transient failures, handle
API timeouts gracefully.

## 64. Security

Validate every request server-side (never trust frontend validation alone).
Sanitize filenames. Limit upload size. Validate MIME types. API key lives
only on the backend. CORS restricted to allowed origins.

## 65. Logging

Dev: INFO/DEBUG/ERROR. Prod: ERROR/WARNING only. Never log API keys,
uploaded file contents, user audio, or personal data.

## 66. Code Quality Standards

TypeScript strict mode, no `any`, ESLint + Prettier, consistent imports,
absolute import aliases, zero TS errors, zero `console.log` in production.

## 67. Testing Strategy

**Frontend:** component tests, interaction tests, responsive testing.
**Backend:** API endpoint tests, validation tests, error handling tests.
**Manual:** OCR upload, PDF upload, speech recording, theme switching, mobile
responsiveness, keyboard navigation.

## 68. Build & Deployment

**Frontend:** build passes with zero warnings, optimized production bundle,
compressed static assets.
**Backend:** environment-driven config, health check endpoint,
production-ready Uvicorn config.

## 69. Definition of Engineering Done

Functionality works · UI matches design system · responsive · accessible ·
zero TS/lint errors · tested · performance reviewed · error states handled ·
loading states implemented · docs updated.

## 70. Claude Code Engineering Rules

- Build incrementally in phases; test each phase before proceeding.
- Never leave TODO placeholders.
- Refactor duplicated code immediately.
- Keep components modular and reusable.
- Prioritize performance over unnecessary abstraction.
- Follow the design system exactly.
- Every commit leaves the project in a runnable state.

---
**Author:** Pranjul Rathour
**Designation:** GenAI Engineer
**Organization:** NEXT UPGRAD WEB SOLUTIONS
