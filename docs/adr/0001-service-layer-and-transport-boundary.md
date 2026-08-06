# ADR 0001: Service-Layer Boundary Between Frontend and Mistral AI

## Context

The app needs two Mistral AI capabilities (OCR, Voxtral Speech-to-Text) and
must be extensible to more (translation, chat, document Q&A, vision) without
rearchitecting. The PRD (`docs/prd/04-architecture.md` §42, §90) mandates
that the frontend never talk to Mistral directly.

## Decision

- All Mistral calls go through a FastAPI backend, never from the browser.
- The backend isolates the Mistral SDK behind a service layer
  (`app/services/mistral_ocr.py`, `app/services/mistral_speech.py`) so a
  vendor SDK change or provider swap only touches that layer.
- Every endpoint returns the same response envelope
  (`{ success, data | fields..., message }`), so new capabilities (future
  routers) plug into the same frontend `services/*.service.ts` pattern
  without bespoke handling.
- Live speech transcription uses a WebSocket (`/api/v1/speech/live`) as the
  primary path, with file-upload transcription (`/api/v1/speech/transcribe`)
  as a fallback/alternate flow — not a replacement.

## Consequences

- **Why this over calling Mistral from the browser:** keeps the API key
  server-side only (PRD §64/§92 security requirement) and lets us normalize
  errors/timeouts/retries in one place instead of duplicating that logic in
  the client.
- **Why a service layer instead of calling the SDK in routers:** routers
  become thin and testable; swapping OCR/STT providers later means editing
  one file, not hunting through route handlers.
- Adds one network hop (frontend → backend → Mistral) versus calling Mistral
  directly — accepted trade-off for security and future extensibility.

## Alternatives Considered

- **Direct browser-to-Mistral calls.** Rejected: leaks the API key to the
  client and violates the PRD's non-negotiable security requirement.
- **Single monolithic "ai_service.py" for all capabilities.** Rejected: PRD
  §97 requires each capability to own its router + service so adding
  translation/chat/vision later doesn't touch OCR/Speech code.

---
**Author:** Pranjul Rathour
**Designation:** GenAI Engineer
**Organization:** NEXT UPGRAD WEB SOLUTIONS
