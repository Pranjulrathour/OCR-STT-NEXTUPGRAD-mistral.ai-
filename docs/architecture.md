# Architecture

Full narrative lives across the PRD; this page is the quick-reference map.

## Layering

```
Browser
  → Next.js (Server Components by default; Client Components only for
     ThemeToggle, OCR upload, Speech recorder — PRD §57)
  → Component → Service (frontend/services/*.service.ts) → lib/api.ts
  → FastAPI (backend/app/api/*.py — thin routers, no business logic)
  → Service (backend/app/services/mistral_*.py — the only Mistral SDK callers)
  → Mistral OCR / Voxtral API
```

The frontend never calls Mistral directly (ADR 0001). Every response follows
the standard envelope (PRD §85).

## Why a service layer on both sides

- **Frontend:** `services/*.service.ts` isolate `fetch`/`WebSocket` calls so
  components stay presentation-only, and so a backend contract change is a
  one-file fix (PRD §50/§51).
- **Backend:** `services/mistral_*.py` isolate the Mistral SDK so routers
  stay thin and a vendor SDK change doesn't ripple into request validation
  or response shaping (PRD §90, ADR 0001).

## Config

Both sides are environment-driven — `NEXT_PUBLIC_API_URL` on the frontend,
the full list in `backend/.env.example` on the backend. Nothing is
hardcoded; see PRD §53/§91.

## Live speech streaming — verified against the installed SDK

`mistralai==2.9.1` exposes genuine realtime transcription:
`client.audio.realtime.transcribe_stream(audio_stream, model, audio_format)`
opens a WebSocket to Mistral internally and yields incremental
`TranscriptionStreamTextDelta` events. `backend/app/services/mistral_speech.py`
bridges the browser's WebSocket directly into this — no polling/rebuffering
hack. One hard requirement this imposes: **the realtime API only accepts raw
PCM audio** (`pcm_s16le` at 16kHz, per `LIVE_AUDIO_ENCODING`/
`LIVE_AUDIO_SAMPLE_RATE` in that module) — not a compressed container. The
frontend's Speech module must capture audio via the Web Audio API
(`AudioContext`/`AudioWorklet`) and send raw PCM16 frames, **not**
`MediaRecorder`'s default webm/opus output, or the backend will reject/fail
to decode the stream.

**Second hard requirement, found only by testing against the live API:** the
realtime endpoint needs its own model id — `voxtral-mini-transcribe-realtime-2602`
(`STT_REALTIME_MODEL`) — not the batch/file model
(`voxtral-mini-latest`, `STT_MODEL`). Using the batch model for the realtime
call gets an HTTP 403 with no explanatory body; there was no way to
distinguish "wrong model" from "no beta access" without checking Mistral's
own docs. Both `/api/v1/speech/transcribe` (file) and `/api/v1/speech/live`
(realtime) have been run end-to-end against the real API with real spoken
audio (Windows SAPI TTS → 16kHz PCM WAV) and produced an exact-match
transcript both ways.

## Speech accuracy/latency features (added after real user testing)

- **Tunable streaming latency** — `STT_STREAMING_DELAY_MS` (default 250ms)
  is passed straight through to `transcribe_stream`'s
  `target_streaming_delay_ms`. Lower feels snappier; higher gives the model
  more audio context per word before committing to it.
- **Post-stop accuracy refinement** — controlled by `STT_REFINE_AFTER_STOP`.
  The realtime model is tuned for low latency, which typically trades away
  some accuracy a full-context batch pass doesn't have to. The WS handler
  (`app/api/speech.py`) buffers every PCM chunk it forwards, and once the
  client sends `"stop"`, wraps the buffered audio as a WAV
  (`app/utils/audio.py::pcm16_to_wav`) and re-transcribes it with the batch
  model (`STT_MODEL`). The client sees `{"status":"refining"}` then
  `{"refined_transcript", "language", "model"}` and swaps the transcript in
  — verified end-to-end: live chunks stream in, then the refined pass
  replaces them with an exact-match final transcript.
- **Live language detection** — `TranscriptionStreamLanguage` events are
  forwarded as `{"language": str}` frames and shown as a badge in the UI.
- **Live audio level** — the AudioWorklet computes RMS per block and posts
  it (throttled to ~30fps) alongside PCM audio; the mic UI pulses with
  actual input level instead of a fixed animation loop.
- **Space bar shortcut** — starts/stops recording from anywhere on the
  Speech page (PRD §131), ignored while focus is in a text input.

## Book-scale OCR — batched pages with real progress

The original OCR path was one synchronous call: 20MB cap, 30s timeout, one
`markdown` blob back. That's fine for a page, not a scanned book. Verified
against the installed SDK before building this: `client.ocr.process_async`
accepts `pages=[...]` — a specific list of page indices — so a document can
be OCR'd in batches instead of one all-or-nothing call.

- `WS /api/v1/ocr/live` (`app/api/ocr.py`) is the UI-facing path: client
  sends `{"filename", "content_type", "size"}` then the file as **many**
  fixed-size binary frames (`UPLOAD_CHUNK_BYTES` = 512KB, matched on the
  frontend); server streams `{"total_pages"}` → repeated `{"pages_done",
  "total_pages"}` → `{"result"}` (or `{"error"}`). `POST /api/v1/ocr`
  (unchanged, single-shot) stays for programmatic callers that don't need
  progress.
- **Found by testing with a real 40MB scanned book, not a synthetic file:**
  the first version sent the whole file as one WS binary frame, which hit
  uvicorn's default 16MB `ws_max_size` and silently broke the connection —
  no exception the caller could act on, just a dead upload. Rather than
  bump a CLI flag that every deployment (dev, Docker, prod) would have to
  remember to set identically, the upload is chunked at 512KB per frame
  (`_receive_chunked_upload`) so max upload size is governed only by
  `MAX_UPLOAD_SIZE_MB`, never by a transport default someone forgot to
  raise. Also found in the same test: a 30s per-*batch* timeout is nowhere
  near enough for 20 image-heavy scanned pages — replaced with
  `ocr_batch_timeout_seconds(page_count)`, scaling at `OCR_SECONDS_PER_PAGE`
  (default 15s/page) with a 60s floor.
- Verified against a real 42-page, 40MB scanned biology textbook chapter
  (not synthetic) end-to-end through the actual browser UI: full extraction
  in ~60s, correct table of contents, working page navigation, and
  cross-book search returning accurate per-page match counts.
- Total page count is read locally via `pypdf` before any Mistral call —
  Mistral's response has no "total pages in the source document" field
  independent of what was requested (`app/services/mistral_ocr.py`,
  `compute_page_batches`). Batch size (`OCR_BATCH_PAGES`, default 20) and a
  hard cap (`OCR_MAX_PAGES`, default 1500) are both configurable.
- Images degenerate to a single "1 of 1" batch through the same code path
  — no separate fast/slow implementation to keep in sync.
- `max_upload_size_mb` default raised 20 → 100 (scanned books run large).
- Verified end-to-end against the live API with a real 5-page multi-image
  PDF at `OCR_BATCH_PAGES=2` (forcing 3 batches): progress events arrived
  in order (`2 of 5` → `4 of 5` → `5 of 5`), and each page's content landed
  on the correct page index across batch boundaries.
- Frontend: `OcrResultView` renders the existing tabbed Markdown/Plain Text
  view only for single-page results; multi-page results get `BookReader`
  (`frontend/components/ocr/book-reader.tsx`) — a table of contents parsed
  from markdown headings per page, page-by-page navigation, and
  search-across-the-book with match highlighting, in a constrained
  reading-width column instead of one giant scrollable blob.

## Local CORS — any localhost port, not just 3000

`next dev` picks a random port whenever 3000 is taken, and `backend/app/middleware/cors.py`
used to require an exact match in `CORS_ORIGINS`, which broke as soon as the
frontend landed on a different port ("Connection lost" in the UI — it's a
CORS rejection, not a real network failure). In `local` environment only,
`allow_origin_regex` now accepts any `http(s)://localhost:<port>` /
`127.0.0.1:<port>` origin; staging/production still use the explicit
allowlist exclusively.

## Verified Mistral SDK surface (not guessed)

The service layer's exact calls — `client.ocr.process_async`,
`client.audio.transcriptions.complete_async`,
`client.audio.realtime.transcribe_stream` — and every field name read off
their responses (`OCRPageObject.markdown`, `TranscriptionResponse.text` /
`.language` / `.usage.prompt_audio_seconds`,
`TranscriptionStreamTextDelta.text`) were confirmed by introspecting the
installed `mistralai==2.9.1` package directly, not assumed from memory, and
then confirmed again by running real requests against the live API (not just
"it type-checks"). If the pinned SDK version changes, re-run that
introspection before trusting these field names again — see the module
docstrings in `mistral_ocr.py` / `mistral_speech.py` for the exact approach.

---
**Author:** Pranjul Rathour
**Designation:** GenAI Engineer
**Organization:** NEXT UPGRAD WEB SOLUTIONS
