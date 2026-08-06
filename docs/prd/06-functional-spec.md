# Part 6 — OCR Module & Speech-to-Text Module Functional Specifications

## 99. Feature Overview

**Module A — Mistral OCR:** extract structured text from PDFs, images, and
scanned documents.

**Module B — Realtime Speech-to-Text:** convert live speech into text using
Mistral Voxtral with low latency and an exceptional UX.

---

## MODULE 1 — Mistral OCR

### 100. OCR User Flow

Landing → OCR tab → drag & drop / upload → client validation → file preview
→ Extract Text → backend upload → Mistral OCR → streaming progress →
formatted result → copy / download / share. No page refresh; the whole flow
feels seamless.

### 101. Upload Area

Supports drag & drop and click-to-upload. Accepted: PDF, PNG, JPG, JPEG.

Visual states: Default, Hover, Dragging, Uploading, Success, Failure. On
drag: border changes, background brightens slightly, upload icon animates.

### 102. Validation Rules

Max size **20 MB**. Reject: empty file, corrupted file, unsupported format,
password-protected PDF, zero-byte file — with a friendly message. Never
upload invalid files to the backend.

### 103. Upload Experience

On file select, immediately show filename, size, type, remove button,
replace button — **no backend call yet**. The backend call only starts after
the user clicks **Extract**.

### 104. Processing Timeline

Uploading... → Reading document... → Sending to Mistral... → Extracting
text... → Formatting output... → Completed. Each stage animated.

### 105. Result Layout

Header: document name, processing time, pages, characters, words. Body:
Markdown / Plain Text tabs. Footer: Copy, Download.

### 106. Output Tabs

Markdown and Plain Text — instant client-side switching, no re-fetch.

### 107. Toolbar

Copy, Download TXT, Download MD, Clear Result, New Upload — each with a tooltip.

### 108. Statistics

Document name, pages, characters, words, estimated reading time, processing
time, model used.

### 109. Download

Formats: TXT, Markdown. Filename pattern: `filename_extracted.txt` /
`filename_extracted.md`.

### 110. Clipboard

Copy button copies the currently active tab's content. Toast: "Copied successfully."

### 111. Error Cases

File too large, unsupported format, OCR timeout, no text detected, server
unavailable, network disconnected — each with a Retry button and a friendly
message (never a raw error).

### 112. Empty State

Document icon + "Drop a PDF or Image to begin extracting text."

### 113. Success State

Green check animation + processing summary.

---

## MODULE 2 — Speech-to-Text

### 114. Speech User Flow

Landing → Speech tab → grant microphone → ready → Start Recording → live
transcript → Pause → Resume → Stop → Copy → Download.

### 115. Microphone Permissions

States: Unknown, Prompting, Granted, Denied. The denied screen must explain
how to re-enable the mic permission in the browser.

### 116. Recording Controls

Start, Pause, Resume, Stop, Clear — with correctly handled disabled states
(e.g. Pause disabled when not recording).

### 117. Recording Indicator

Large animated-pulse microphone icon, recording timer, red indicator while active.

### 118. Live Transcript

Updates continuously; **append-only**, never replaces previous content;
smooth auto-scroll.

### 119. Transcript Toolbar

Copy, Download TXT, Clear, Share (future).

### 120. Transcript Statistics

Characters, words, sentences, recording duration, language, model, latency.

### 121. Pause Behaviour

Pause stops sending audio. Resume continues the **same** transcript — never
starts a new one.

### 122. Stop Behaviour

Stops the stream and locks the transcript, after which Copy/Download/Clear
remain available.

### 123. Download Transcript

TXT now; Markdown/PDF are future scope. Filename pattern: `speech_YYYY-MM-DD.txt`.

### 124. Auto-Scroll

Always scrolls to bottom unless the user has manually scrolled up; resumes
auto-scroll once the user scrolls back to the bottom.

### 125. Streaming Behaviour

Incoming chunk → append → animate appearance → continue listening. Transcript
is never cleared mid-stream.

### 126. Connection States

Disconnected, Connecting, Listening, Streaming, Paused, Stopped — every state
must be visibly represented in the UI.

### 127. Speech Errors

Microphone denied, network timeout, streaming disconnected, audio device
unavailable, model unavailable — each with retry options.

### 128. Clear Transcript

Requires a confirmation dialog ("Delete transcript?" Cancel / Delete) to
prevent accidental loss.

### 129. Empty State

Microphone icon + "Press Start Recording to begin transcription."

---

## Shared Features

### 130. Theme

Light / Dark / System across both modules, with zero layout shift on switch.

### 131. Keyboard Shortcuts

OCR: Ctrl+O upload, Ctrl+C copy, Ctrl+D download.
Speech: Space start/stop, Esc close dialog, Delete clear.

### 132. Notifications

Toast system for: Upload Complete, Copied, Downloaded, Recording Started,
Recording Stopped, Microphone Enabled.

### 133. Accessibility

Screen readers, keyboard navigation, ARIA labels, visible focus, color
contrast, accessible icons.

### 134. Edge Cases

**OCR:** huge PDFs, blank pages, rotated documents, low-quality scans, mixed
image/PDF uploads, multiple rapid uploads, slow network.

**Speech:** tab switch mid-recording, microphone disconnected, browser loses
focus, long silence, browser refresh, network interruption, rapid
start/stop.

The application must fail gracefully in every one of these.

### 135. Acceptance Criteria

**OCR**
- Upload works for all supported formats.
- Validation prevents invalid uploads.
- Progress visible throughout processing.
- Text extracted successfully.
- Markdown and Plain Text views available.
- Copy and download work reliably.
- Statistics accurate.
- Errors are user-friendly.
- Responsive on mobile and desktop.

**Speech-to-Text**
- Microphone permission handled correctly.
- Recording starts within one second.
- Transcript updates in real time.
- Pause/Resume function correctly.
- Stop finalizes the transcript.
- Copy and download work.
- Statistics update live.
- Connection interruptions handled gracefully.
- Responsive and accessible across devices.

### 136. Future Scope (explicitly out of current MVP)

Audio file transcription, translation, speaker diarization, summarization,
OCR search, document comparison, chat with extracted text, export to
PDF/DOCX, history & favorites, multi-language UI.

**Do not implement these now** — but the architecture (service-layer
abstraction, router-per-capability, standard response envelope) must make
adding them later a non-refactor.

## Deliverable

Both modules implemented with production-quality UX, robust validation,
graceful error handling, responsive layouts, accessible interactions,
optimized for clarity, performance, and extensibility — reading as a premium
AI productivity tool, not a technology demo.

---
**Author:** Pranjul Rathour
**Designation:** GenAI Engineer
**Organization:** NEXT UPGRAD WEB SOLUTIONS
