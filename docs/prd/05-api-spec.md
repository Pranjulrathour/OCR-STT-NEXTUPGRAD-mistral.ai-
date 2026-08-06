# Part 5 — Backend API Specification, Mistral Integration, Streaming Architecture & API Contracts

## 71–72. Backend Philosophy & Responsibilities

The backend is not just a proxy. It owns: security, validation, error
handling, rate limiting (future), logging, streaming, response formatting,
API versioning, service abstraction. It must validate every request, verify
uploaded files, manage Mistral auth, normalize responses, handle retries,
return consistent JSON schemas, stream STT where available, log errors
safely, and prevent API key exposure.

## 73. Backend Architecture

```
Client → FastAPI → Router → Controller → Service Layer → Mistral Client → Mistral API
```

Business logic lives **only** in the service layer.

## 74. Folder Structure (authoritative — supersedes Part 4 §46 sketch)

```
backend/
  app/
    api/
      ocr.py
      speech.py
      health.py
    services/
      mistral_ocr.py
      mistral_speech.py
    schemas/
      request.py
      response.py
    middleware/
      logging.py
      cors.py
    core/
      config.py
      constants.py
    utils/
      validators.py
      file.py
    main.py
```

## 75. API Versioning

All endpoints prefixed `/api/v1/`. Future breaking changes go to `/api/v2/`
without breaking existing clients.

## 76. Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Liveness/readiness check |
| POST | `/api/v1/ocr` | Extract text from PNG/JPG/JPEG/PDF |
| POST | `/api/v1/speech/transcribe` | Audio file transcription |
| WS | `/api/v1/speech/live` | Real-time streaming transcription |

**Health response:**
```json
{ "status": "healthy", "version": "1.0.0" }
```

## 77–78. OCR Request Flow & Validation

```
User → Upload File → Frontend Validation → FastAPI → File Validation
     → Mistral OCR → Formatting → Frontend
```

**Allowed:** pdf, png, jpg, jpeg. **Reject:** exe, zip, apk, js, mp4, and any
other type. **Max upload:** 20 MB (configurable via settings).

## 79–80. OCR Response

**Success:**
```json
{
  "success": true,
  "filename": "invoice.pdf",
  "pages": 3,
  "markdown": "....",
  "plain_text": "....",
  "processing_time": 1.42
}
```
Always return both markdown and plain text.

**Failure:**
```json
{ "success": false, "message": "Unsupported file format" }
```
Never expose raw Mistral exceptions to the client.

## 81–82. Speech Request Flow & Live Streaming Architecture

**File-based flow:** Microphone → MediaRecorder → Audio Chunks → FastAPI →
Mistral Voxtral → Transcript → Frontend

**Preferred (streaming):**
```
Microphone → WebSocket → FastAPI → Mistral → Streaming Response → Frontend
```

**Fallback:** Record → Upload Audio → Mistral → Transcript. Streaming is the
default implementation if the model/SDK supports it.

## 83. Speech Response (file transcription)

```json
{
  "success": true,
  "transcript": "Hello everyone...",
  "language": "en",
  "duration": 15.2,
  "processing_time": 0.87
}
```

## 84. Streaming Response (WS chunks)

```json
{ "chunk": "Hello" }
{ "chunk": " everyone" }
{ "chunk": " welcome..." }
```

Frontend appends each chunk immediately — never replaces the previous transcript.

## 85. Standard Response Wrapper

Every endpoint follows the same envelope.

**Success:**
```json
{ "success": true, "data": {}, "message": "Success" }
```

**Failure:**
```json
{ "success": false, "message": "Validation failed" }
```

Consistency across all endpoints is mandatory.

## 86. Request Validation

Reject before calling Mistral: empty files, invalid MIME types, oversized
uploads, missing parameters, corrupted PDFs, empty audio, invalid audio
encoding.

## 87. Timeout Strategy

| Endpoint | Timeout |
|---|---|
| OCR | 30s |
| Speech | 60s |

Timeout response: `{ "success": false, "message": "Processing timeout" }`

## 88. Retry Policy

**Retry:** transient network failures, 5xx responses, connection resets.
**Never retry:** invalid requests, auth errors, unsupported file types.
**Max retries:** 3, with exponential backoff.

## 89. Logging Strategy

Dev: INFO/DEBUG/ERROR. Prod: ERROR/WARNING. Never log API keys, uploaded
file contents, user audio, or personal data.

## 90. Mistral Service Layer Abstraction

```
OCR Router → OCR Service → Mistral Client → Mistral OCR
```

If Mistral changes its SDK, only the client layer needs updates — routers
and services depend on an internal port, not the vendor SDK directly.

## 91. Configuration

```env
MISTRAL_API_KEY=
MISTRAL_BASE_URL=
OCR_MODEL=
STT_MODEL=
HOST=
PORT=
```

No hardcoded configuration — everything through `pydantic-settings`.

## 92. Security

Sanitize filenames/metadata/MIME types. Restrict file extensions, upload
size, request body size. Never persist uploaded files unless explicitly
required; delete temp files immediately after processing.

## 93. Middleware

CORS, request logging, response timing, error handling, security headers,
request-ID generation. Every request gets a unique request ID for debugging.

## 94. Performance Requirements

- Health endpoint < 50ms
- OCR endpoint overhead < 100ms (excluding AI processing time)
- STT endpoint overhead < 100ms
- Efficient async I/O, non-blocking file handling, connection reuse

## 95. API Documentation

Swagger UI + ReDoc, kept in sync with implementation. Include endpoint
descriptions, request/response examples, error codes.

## 96. Error Code Matrix

| HTTP Status | Meaning | User Message |
|---|---|---|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid input provided |
| 401 | Unauthorized | Authentication failed |
| 413 | Payload Too Large | File exceeds maximum size |
| 415 | Unsupported Media Type | Unsupported file format |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Error | Something went wrong |
| 503 | Service Unavailable | AI service temporarily unavailable |

Never expose stack traces in API responses.

## 97. Future Extensibility

New capabilities (Translation, Summarization, Chat, Document Q&A, Vision,
Image Understanding) each get their own router + service, following the same
request/response conventions — without touching existing endpoints.

## 98. Backend Quality Checklist

- [ ] All endpoints validated
- [ ] Async implementation where appropriate
- [ ] Consistent response schema
- [ ] Temp files cleaned up
- [ ] Timeouts handled
- [ ] Retries implemented
- [ ] Security checks in place
- [ ] API docs updated
- [ ] Zero sensitive data leakage
- [ ] Structured logging enabled

---
**Author:** Pranjul Rathour
**Designation:** GenAI Engineer
**Organization:** NEXT UPGRAD WEB SOLUTIONS
