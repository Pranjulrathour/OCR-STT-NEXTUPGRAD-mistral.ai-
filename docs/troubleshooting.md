# Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `503 AI service temporarily unavailable` from `/api/v1/ocr` or `/api/v1/speech/*` | `MISTRAL_API_KEY` unset in `backend/.env` | Set it, restart the backend |
| Settings page shows API Status "Unavailable" | Backend not running, or `NEXT_PUBLIC_API_URL` points at the wrong host/port | Start the backend; check `frontend/.env.local` |
| `415 Unsupported file format` on a real PDF/image | Browser sent an unexpected `Content-Type`, or file extension doesn't match `ALLOWED_OCR_EXTENSIONS` | Confirm the file is actually `.pdf/.png/.jpg/.jpeg` and not renamed |
| OCR shows "Connection lost. Check your network and try again." even though the backend is up | CORS rejection, not a real network failure — `fetch` reports any CORS-blocked response as a generic network error. In `local` env this should now be handled automatically (any `localhost:<port>` is allowed); in `staging`/`production` the frontend's origin must be in `CORS_ORIGINS` | Check the backend log for `Disallowed CORS origin`; add the exact origin to `CORS_ORIGINS` if not `local` |
| WebSocket to `/api/v1/speech/live` closes immediately | `MISTRAL_API_KEY` unset (server sends an error frame then closes) | Check backend logs for the `X-Request-ID` in the failed request; verify `.env` |
| Speech transcript looks slightly different right after Stop | Expected — the post-stop accuracy-refinement pass (`STT_REFINE_AFTER_STOP=true`) replaces the live transcript with a full-context re-transcription; watch for the "Refining…" badge | Not a bug; disable via `STT_REFINE_AFTER_STOP=false` if you'd rather keep the live-only version |
| `npm run build` fails after pulling latest | Dependency drift | `rm -rf node_modules && npm install` |
| Backend `ImportError` for `mistralai` | Venv not activated / deps not installed | `pip install -e ".[dev]"` inside `backend/.venv` |

Every backend response includes an `X-Request-ID` header — quote it when
reporting a bug so the matching structured log line can be found.

---
**Author:** Pranjul Rathour
**Designation:** GenAI Engineer
**Organization:** NEXT UPGRAD WEB SOLUTIONS
